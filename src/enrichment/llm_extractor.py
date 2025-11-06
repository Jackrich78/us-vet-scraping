"""
LLM-based data extraction using OpenAI structured outputs.

This module extracts structured veterinary practice data from website content
using OpenAI's gpt-4o-mini with beta.chat.completions.parse() for guaranteed
valid JSON responses.

Features:
- OpenAI structured outputs (100% valid JSON, no parsing errors)
- Token counting BEFORE API calls with tiktoken
- Budget enforcement with hard abort at $1.00
- Text truncation for cost control (8000 chars ~= 2000 tokens)
- Temperature=0.1 for deterministic extraction

Usage:
    extractor = LLMExtractor(cost_tracker=tracker, config=openai_config)

    extraction = await extractor.extract_practice_data(
        practice_name="Example Vet",
        website_pages=[page1, page2, page3]
    )
"""

import asyncio
from typing import List, Optional
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import ValidationError

from src.models.enrichment_models import VetPracticeExtraction, WebsiteData
from src.utils.cost_tracker import CostTracker, CostLimitExceeded
from src.config.config import OpenAIConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LLMExtractor:
    """Extract structured data from website content using OpenAI.

    Uses OpenAI beta.chat.completions.parse() with Pydantic models to guarantee
    100% valid JSON responses. Counts tokens BEFORE API calls and enforces budget.

    Attributes:
        cost_tracker: CostTracker for budget enforcement
        config: OpenAI configuration (model, temperature, etc.)
        client: Async OpenAI client
        extraction_prompt: System prompt for data extraction
    """

    # Text truncation limit (8000 chars ~= 2000 tokens for cost control)
    MAX_TEXT_LENGTH = 8000

    # Estimated output tokens for typical extraction (validated via spike: ~300)
    ESTIMATED_OUTPUT_TOKENS = 300

    def __init__(
        self,
        cost_tracker: CostTracker,
        config: OpenAIConfig,
        prompt_file: str = "config/website_extraction_prompt.txt"
    ):
        """Initialize LLM extractor.

        Args:
            cost_tracker: CostTracker for budget monitoring
            config: OpenAI configuration
            prompt_file: Path to extraction prompt file

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        self.cost_tracker = cost_tracker
        self.config = config

        # Load extraction prompt
        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            raise FileNotFoundError(f"Extraction prompt not found: {prompt_file}")

        self.extraction_prompt = prompt_path.read_text(encoding='utf-8')
        logger.debug(f"Loaded extraction prompt from {prompt_file}")

        # Initialize async OpenAI client
        self.client = AsyncOpenAI(api_key=config.api_key)

        logger.info(
            f"LLMExtractor initialized: model={config.model}, "
            f"temp={config.temperature}, budget=${cost_tracker.budget_limit:.2f}"
        )

    def _extract_page_type(self, url: str) -> str:
        """Extract page type from URL for priority ordering.

        Args:
            url: Page URL

        Returns:
            Page type identifier
        """
        url_lower = url.lower()

        if "team" in url_lower or "staff" in url_lower or "doctor" in url_lower or "veterinarian" in url_lower:
            return "team"
        elif "about" in url_lower:
            return "about"
        elif "service" in url_lower:
            return "services"
        elif "contact" in url_lower or "location" in url_lower:
            return "contact"
        else:
            return "homepage"

    def _prepare_website_text(self, pages: List[WebsiteData]) -> str:
        """Prepare website content for extraction with document-based budget allocation.

        Uses page priority ordering to preserve high-value content (team/about pages)
        and prevent homepage verbosity from truncating important decision-maker data.

        Budget allocation:
        - Team Page: 3000 chars (highest priority - contains vet names)
        - About Page: 2500 chars (decision maker info, history)
        - Homepage: 2000 chars (overview)
        - Services Page: 1000 chars (specialties, technology)
        - Other Pages: 500 chars (contact, hours)

        Args:
            pages: List of scraped website pages

        Returns:
            Prioritized and budget-allocated website text
        """
        if not pages:
            return ""

        # Sort pages by importance (team > about > services > contact > homepage)
        page_priority = {
            "team": 1,
            "about": 2,
            "services": 3,
            "contact": 4,
            "homepage": 5
        }

        sorted_pages = sorted(
            pages,
            key=lambda p: page_priority.get(self._extract_page_type(p.url), 99)
        )

        # Build text with page-specific character budgets
        page_budgets = {
            "team": 3000,
            "about": 2500,
            "services": 1000,
            "contact": 500,
            "homepage": 2000
        }

        page_texts = []
        remaining_budget = self.MAX_TEXT_LENGTH

        for page in sorted_pages:
            page_type = self._extract_page_type(page.url)
            page_budget = page_budgets.get(page_type, 500)

            # Allocate budget proportionally if total exceeds limit
            if remaining_budget <= 0:
                logger.debug(
                    f"Reached character budget limit. Stopped after {len(page_texts)} pages. "
                    f"Prioritized: {', '.join(pt.split('===')[1].split('PAGE')[0].strip() for pt in page_texts)}"
                )
                break

            # Use allocated budget for this page
            actual_budget = min(page_budget, remaining_budget)
            page_content = page.content[:actual_budget]

            page_type_display = page_type.upper()
            page_texts.append(
                f"=== {page_type_display} PAGE ===\n{page_content}\n"
            )
            remaining_budget -= len(page_content)

        combined_text = "\n".join(page_texts)

        if len(combined_text) > self.MAX_TEXT_LENGTH:
            # Final safety truncation (shouldn't happen with budget allocation)
            combined_text = combined_text[:self.MAX_TEXT_LENGTH]
            logger.debug(
                f"Final truncation: {len(combined_text):,} chars (budget allocation applied)"
            )

        return combined_text

    async def extract_practice_data(
        self,
        practice_name: str,
        website_pages: List[WebsiteData]
    ) -> Optional[VetPracticeExtraction]:
        """Extract structured data from practice website pages.

        Counts tokens BEFORE API call, checks budget, then calls OpenAI with
        structured outputs. Tracks actual cost after completion.

        Args:
            practice_name: Practice name (for logging)
            website_pages: List of scraped website pages

        Returns:
            VetPracticeExtraction if successful, None if failed

        Raises:
            CostLimitExceeded: If budget would be exceeded
        """
        if not website_pages:
            logger.warning(f"{practice_name}: No website pages to extract from")
            return None

        # Prepare text for extraction
        website_text = self._prepare_website_text(website_pages)

        if not website_text:
            logger.warning(f"{practice_name}: Empty website text after preparation")
            return None

        # Build full prompt
        user_message = f"Practice Name: {practice_name}\n\nWebsite Content:\n{website_text}"
        full_prompt = f"{self.extraction_prompt}\n\n{user_message}"

        # Count tokens and check budget BEFORE API call
        try:
            self.cost_tracker.check_budget(
                input_text=full_prompt,
                estimated_output_tokens=self.ESTIMATED_OUTPUT_TOKENS
            )
        except CostLimitExceeded as e:
            logger.error(f"Budget limit exceeded before extracting {practice_name}: {e}")
            raise  # Propagate to orchestrator for pipeline abort

        # Log token count estimate
        input_token_estimate = self.cost_tracker.count_tokens(full_prompt)
        logger.debug(
            f"{practice_name}: Estimated {input_token_estimate} input tokens + "
            f"{self.ESTIMATED_OUTPUT_TOKENS} output tokens"
        )

        # Call OpenAI with structured outputs
        try:
            logger.debug(f"{practice_name}: Calling OpenAI API...")

            response = await self.client.beta.chat.completions.parse(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.extraction_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format=VetPracticeExtraction,
                temperature=self.config.temperature
            )

            # Extract parsed response
            extraction = response.choices[0].message.parsed

            # Track actual cost
            actual_input_tokens = response.usage.prompt_tokens
            actual_output_tokens = response.usage.completion_tokens
            call_cost = self.cost_tracker.track_call(actual_input_tokens, actual_output_tokens)

            logger.info(
                f"{practice_name}: Extraction successful - "
                f"{actual_input_tokens} input + {actual_output_tokens} output tokens, "
                f"cost=${call_cost:.6f}"
            )

            # Log key extracted data for visibility
            logger.debug(
                f"  Vet count: {extraction.vet_count_total} ({extraction.vet_count_confidence}), "
                f"Decision maker: {extraction.decision_maker.name if extraction.decision_maker else 'None'}, "
                f"Personalization: {len(extraction.personalization_context)} facts"
            )

            return extraction

        except ValidationError as e:
            # This should never happen with structured outputs, but log if it does
            logger.error(
                f"{practice_name}: Pydantic validation failed (unexpected): {e}",
                exc_info=True
            )
            return None

        except Exception as e:
            logger.error(
                f"{practice_name}: OpenAI API call failed: {e}",
                exc_info=True
            )
            return None

    async def extract_batch(
        self,
        practices: List[tuple]
    ) -> dict:
        """Extract data for multiple practices sequentially.

        Note: Extraction is sequential (not concurrent) to ensure budget checking
        happens before each call and we can abort if limit exceeded.

        Args:
            practices: List of (practice_name, website_pages) tuples

        Returns:
            Dictionary mapping practice_name to VetPracticeExtraction:
            {
                "Example Vet": VetPracticeExtraction(...),
                "Another Vet": VetPracticeExtraction(...)
            }

        Raises:
            CostLimitExceeded: If budget limit exceeded during batch
        """
        logger.info(f"Starting batch extraction: {len(practices)} practices")

        results = {}
        successful = 0

        for i, (practice_name, website_pages) in enumerate(practices, 1):
            try:
                extraction = await self.extract_practice_data(practice_name, website_pages)

                if extraction:
                    results[practice_name] = extraction
                    successful += 1
                else:
                    results[practice_name] = None

                # Log progress every 10 practices
                if i % 10 == 0:
                    summary = self.cost_tracker.get_summary()
                    logger.info(
                        f"Progress: {i}/{len(practices)} practices, "
                        f"{successful} successful, "
                        f"cost=${summary['cumulative_cost']:.4f}/${summary['budget_limit']:.2f}"
                    )

            except CostLimitExceeded:
                # Budget limit exceeded - log and abort batch
                logger.error(
                    f"Budget limit exceeded at practice {i}/{len(practices)}: {practice_name}"
                )
                raise  # Propagate to orchestrator

            except Exception as e:
                # Unexpected error - log and continue to next practice
                logger.error(
                    f"Unexpected error extracting {practice_name}: {e}",
                    exc_info=True
                )
                results[practice_name] = None

        # Final summary
        summary = self.cost_tracker.get_summary()
        logger.info(
            f"Batch extraction complete: {successful}/{len(practices)} successful, "
            f"total cost=${summary['cumulative_cost']:.4f}"
        )

        return results

    def get_cost_summary(self) -> dict:
        """Get cost tracking summary.

        Returns:
            Dictionary with cost statistics from CostTracker
        """
        return self.cost_tracker.get_summary()
