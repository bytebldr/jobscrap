"""Verification Test Suite for JobScrap v0.5 Direct Company Career Pipeline."""

import unittest
from jobscrap import CompanyCatalog, CompanyResolver, JobScraper
from jobscrap.pipeline.dedup import deduplicate_jobs
from jobscrap.pipeline.salary import parse_salary
from jobscrap.core.models import JobListing, SalaryRange

class TestJobScrapV05(unittest.TestCase):

    def setUp(self):
        self.catalog = CompanyCatalog()
        self.scraper = JobScraper(catalog=self.catalog)

    def test_catalog_retrieval(self):
        """Verify catalog indexing and fuzzy retrieval."""
        razorpay = self.catalog.get("Razorpay")
        self.assertIsNotNone(razorpay)
        self.assertEqual(razorpay.ats_type, "greenhouse")
        self.assertEqual(razorpay.ats_identifier, "razorpaysoftwareprivatelimited")

        # Fuzzy search by domain
        supabase = self.catalog.get("supabase.com")
        self.assertIsNotNone(supabase)
        self.assertEqual(supabase.ats_type, "ashby")

    def test_greenhouse_live_fetch(self):
        """Verify live extraction from Greenhouse corporate endpoint."""
        jobs = self.scraper.get_company_jobs("Razorpay")
        self.assertGreater(len(jobs), 0)
        self.assertTrue(all(j.company == "Razorpay" for j in jobs))
        self.assertTrue(all("greenhouse.io" in j.url for j in jobs))

    def test_ashby_live_fetch(self):
        """Verify live extraction from Ashby corporate endpoint."""
        jobs = self.scraper.get_company_jobs("Supabase")
        self.assertGreater(len(jobs), 0)
        self.assertTrue(all(j.company == "Supabase" for j in jobs))
        self.assertTrue(all("ashbyhq.com" in j.url for j in jobs))

    def test_smartrecruiters_live_fetch(self):
        """Verify live extraction from SmartRecruiters corporate endpoint."""
        jobs = self.scraper.get_company_jobs("Freshworks")
        self.assertGreater(len(jobs), 0)
        self.assertTrue(all(j.company == "Freshworks" for j in jobs))
        self.assertTrue(all("smartrecruiters.com" in j.url for j in jobs))

    def test_lever_live_fetch(self):
        """Verify live extraction from Lever corporate endpoint."""
        jobs = self.scraper.get_company_jobs("Spotify")
        self.assertGreater(len(jobs), 0)
        self.assertTrue(all(j.company == "Spotify" for j in jobs))
        self.assertTrue(all("lever.co" in j.url for j in jobs))

    def test_salary_parsing(self):
        """Verify Indian LPA/Lakhs and rupee salary parsing."""
        sal1 = parse_salary("12 - 18 LPA")
        self.assertIsNotNone(sal1)
        self.assertEqual(sal1.min_inr, 1200000)
        self.assertEqual(sal1.max_inr, 1800000)

        sal2 = parse_salary("₹45,000 / month")
        self.assertIsNotNone(sal2)
        self.assertEqual(sal2.min_inr, 540000)

    def test_deduplication(self):
        """Verify cross-portal Jaccard clustering."""
        j1 = JobListing(
            id="1", source="custom", source_type="custom",
            company="Razorpay", title="Senior Backend Engineer",
            location="Bengaluru", url="https://razorpay.com/careers/1"
        )
        j2 = JobListing(
            id="2", source="greenhouse", source_type="ats",
            company="Razorpay", title="Senior Backend Engineer",
            location="Bengaluru", url="https://boards.greenhouse.io/razorpay/2"
        )
        deduped = deduplicate_jobs([j1, j2])
        self.assertEqual(len(deduped), 1)
        # Prefers primary ATS over aggregator portal
        self.assertEqual(deduped[0].source_type, "ats")

if __name__ == "__main__":
    unittest.main()
