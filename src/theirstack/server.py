import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import argparse
import os
import asyncio
import logging
from datetime import datetime
import re

from mcp import Tool
import aiohttp
from mcp.server.models import InitializationOptions
import mcp.types as types

from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

@dataclass
class CompactCompanyInfo:
    name: str
    domain: str
    industry: str
    country_code: str
    employee_count_range: str
    is_recruiting_agency: bool

@dataclass 
class CompactJobListing:
    id: int
    job_title: str
    url: str
    date_posted: str
    location: str
    country_code: str
    remote: bool
    hybrid: bool
    salary_string: str
    min_salary_usd: Optional[float]
    max_salary_usd: Optional[float]
    seniority: str
    employment_statuses: List[str]
    easy_apply: bool
    clean_description: str  # Cleaned JD without company fluff
    company: CompactCompanyInfo

@dataclass
class FullJobListing:
    # Full version for JSON storage
    id: int
    job_title: str
    url: str
    final_url: str
    date_posted: str
    location: str
    country: str
    country_code: str
    remote: bool
    hybrid: bool
    salary_string: str
    min_annual_salary_usd: Optional[float]
    max_annual_salary_usd: Optional[float]
    avg_annual_salary_usd: Optional[float]
    seniority: str
    employment_statuses: List[str]
    easy_apply: bool
    description: str
    company: Dict  # Full company info

@dataclass
class UserProfile:
    name: str
    skills: List[str]
    preferred_locations: List[str]
    years_of_experience: Optional[int]

# Compact user profile
COMPACT_USER_PROFILE = UserProfile(
    name="AI/ML Engineer",
    skills=["AI/ML", "NLP", "LLM", "RAG", "LangChain", "PyTorch", "Python", "FastAPI"],
    preferred_locations=["India", "Remote"],
    years_of_experience=4
)

PROMPTS = {
    "search-jobs": types.Prompt(
        name="search-jobs",
        description="Search for AI/ML jobs with specific criteria",
        arguments=[
            types.PromptArgument(
                name="technologies",
                description="Company technology slugs (comma-separated, defaults to 'greenhouse')",
                required=False
            ),
            types.PromptArgument(
                name="countries", 
                description="Country codes (comma-separated, defaults to 'IN')",
                required=False
            ),
            types.PromptArgument(
                name="max_age_days",
                description="Maximum age of job postings in days (default: 7)",
                required=False
            ),
        ],
    ),
    "job-application": types.Prompt(
        name="job-application",
        description="Create job application email draft",
        arguments=[
            types.PromptArgument(
                name="job_id",
                description="Job ID to apply for",
                required=True
            ),
            types.PromptArgument(
                name="custom_message",
                description="Custom message to highlight",
                required=False
            ),
        ],
    ),
}

class JobStackAPI:
    def __init__(self, api_key: str):
        self.base_url = "https://api.theirstack.com/v1"
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.cached_jobs: Dict[int, FullJobListing] = {}
        
    def _clean_job_description(self, description: str) -> str:
        """Extract only relevant JD content, removing company fluff"""
        # Remove common company intro patterns
        patterns_to_remove = [
            r'About\s+[A-Za-z\s]+:.*?(?=(?:Job|Role|Position|Requirements|Responsibilities|What|We\'re|You\'ll))',
            r'Our\s+(?:company|mission|vision|values).*?(?=(?:Job|Role|Position|Requirements|Responsibilities|What|We\'re|You\'ll))',
            r'We\s+are\s+a.*?(?=(?:Job|Role|Position|Requirements|Responsibilities|What|We\'re|You\'ll))',
            r'Company\s+Overview.*?(?=(?:Job|Role|Position|Requirements|Responsibilities|What|We\'re|You\'ll))',
        ]
        
        cleaned = description
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Keep only first 800 chars of cleaned description
        if len(cleaned) > 800:
            cleaned = cleaned[:800] + "..."
            
        return cleaned.strip()
        
    def _extract_compact_company_info(self, company_data: Dict) -> CompactCompanyInfo:
        """Extract minimal company information"""
        return CompactCompanyInfo(
            name=company_data.get("name", "Unknown"),
            domain=company_data.get("domain", ""),
            industry=company_data.get("industry", ""),
            country_code=company_data.get("country_code", ""),
            employee_count_range=company_data.get("employee_count_range", ""),
            is_recruiting_agency=company_data.get("is_recruiting_agency", False)
        )
    
    def _extract_compact_job_listing(self, job_data: Dict) -> CompactJobListing:
        """Extract minimal job information for MCP response"""
        company_info = self._extract_compact_company_info(job_data.get("company_object", {}))
        
        description = job_data.get("description", "")
        clean_description = self._clean_job_description(description)
        
        return CompactJobListing(
            id=job_data.get("id"),
            job_title=job_data.get("job_title", ""),
            url=job_data.get("url", ""),
            date_posted=job_data.get("date_posted", ""),
            location=job_data.get("location", ""),
            country_code=job_data.get("country_code", ""),
            remote=job_data.get("remote", False),
            hybrid=job_data.get("hybrid", False),
            salary_string=job_data.get("salary_string", ""),
            min_salary_usd=job_data.get("min_annual_salary_usd"),
            max_salary_usd=job_data.get("max_annual_salary_usd"),
            seniority=job_data.get("seniority", ""),
            employment_statuses=job_data.get("employment_statuses", []),
            easy_apply=job_data.get("easy_apply", False),
            clean_description=clean_description,
            company=company_info
        )
        
    def _extract_full_job_listing(self, job_data: Dict) -> FullJobListing:
            """Extract full job information for JSON storage"""
            # Get company data and remove specified fields
            company_data = job_data.get("company_object", {}).copy()
            # Remove long array fields, remove unnecessary ones
            company_data.pop("company_keywords", None)
            company_data.pop("technology_slugs", None)
            company_data.pop("technology_names", None)
    
            return FullJobListing(
                id=job_data.get("id"),
                job_title=job_data.get("job_title", ""),
                url=job_data.get("url", ""),
                final_url=job_data.get("final_url", ""),
                date_posted=job_data.get("date_posted", ""),
                location=job_data.get("location", ""),
                country=job_data.get("country", ""),
                country_code=job_data.get("country_code", ""),
                remote=job_data.get("remote", False),
                hybrid=job_data.get("hybrid", False),
                salary_string=job_data.get("salary_string", ""),
                min_annual_salary_usd=job_data.get("min_annual_salary_usd"),
                max_annual_salary_usd=job_data.get("max_annual_salary_usd"),
                avg_annual_salary_usd=job_data.get("avg_annual_salary_usd"),
                seniority=job_data.get("seniority", ""),
                employment_statuses=job_data.get("employment_statuses", []),
                easy_apply=job_data.get("easy_apply", False),
                description=job_data.get("description", ""),
                company=company_data
            )
        
    def _save_to_json(self, data: Dict, prefix: str):
        """Save data to JSON file with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("outputs", exist_ok=True)
        # Create filename with prefix and timestamp
        filename = f"outputs/{prefix}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to {filename}: {str(e)}")
        
    async def search_jobs(self, 
                         technologies: Optional[List[str]] = None,
                         countries: Optional[List[str]] = None,
                         max_age_days: int = 7,
                         page: int = 0,
                         limit: int = 50) -> Dict[str, Any]:
        
        titles = ["AI", "ML", "Machine", "NLP", "Applied"]
        
        if not technologies:
            technologies = ["greenhouse"]
        if not countries:
            countries = ["IN"]
            
        payload = {
            "include_total_results": False,
            "order_by": [{"desc": True, "field": "num_jobs"}],
            "posted_at_max_age_days": max_age_days,
            "company_technology_slug_or": technologies,
            "job_country_code_or": countries,
            "job_title_or": titles,
            "page": page,
            "limit": limit,
            "blur_company_data": False
        }
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(f"{self.base_url}/jobs/search", json=payload) as response:
                    if response.status == 200:
                        raw_data = await response.json()
                        # Save full response to JSON
                        self._save_to_json(raw_data, "job_search_full")
                        
                        # Process jobs for both compact and full storage
                        compact_jobs = []
                        full_jobs = []
                        
                        if "data" in raw_data:
                            for job_data in raw_data["data"]:
                                try:
                                    # Create both versions
                                    compact_job = self._extract_compact_job_listing(job_data)
                                    full_job = self._extract_full_job_listing(job_data)
                                    
                                    compact_jobs.append(asdict(compact_job))
                                    full_jobs.append(asdict(full_job))
                                    
                                    # Cache full job
                                    self.cached_jobs[full_job.id] = full_job
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing job {job_data.get('id', 'unknown')}: {str(e)}")
                                    continue
                        
                        # Save processed jobs
                        processed_data = {
                            "metadata": raw_data.get("metadata", {}),
                            "jobs": full_jobs,
                            "search_criteria": {
                                "titles": titles,
                                "technologies": technologies, 
                                "countries": countries,
                                "max_age_days": max_age_days
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        self._save_to_json(processed_data, "job_search_processed")
                        
                        # Return compact version for MCP
                        return {
                            "total_jobs": len(compact_jobs),
                            "jobs": compact_jobs[:10],  # Limit to first 10 for context
                            "search_criteria": {
                                "technologies": technologies,
                                "countries": countries,
                                "max_age_days": max_age_days
                            }
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Error searching jobs: {response.status} - {error_text}")
                        return {"error": f"API request failed: {response.status}"}
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return {"error": str(e)}
    
    def get_cached_job(self, job_id: int) -> Optional[FullJobListing]:
        """Get full cached job by ID"""
        return self.cached_jobs.get(job_id)

async def main(api_config_path: str):
    # Load API configuration
    try:
        with open(api_config_path, 'r') as f:
            config = json.load(f)
            api_key = config.get('api_key')
            if not api_key:
                raise ValueError("API key not found in config file")
    except Exception as e:
        logger.error(f"Error loading API config: {str(e)}")
        raise
    
    job_api = JobStackAPI(api_key)
    server = Server("jobstack")

    @server.list_prompts()
    async def list_prompts() -> List[types.Prompt]:
        return list(PROMPTS.values())

    @server.get_prompt()
    async def get_prompt(
        name: str, arguments: Dict[str, str] | None = None
    ) -> types.GetPromptResult:
        if name not in PROMPTS:
            raise ValueError(f"Prompt not found: {name}")

        if name == "search-jobs":
            technologies = [t.strip() for t in arguments.get("technologies", "").split(",")] if arguments.get("technologies") else None
            countries = [c.strip() for c in arguments.get("countries", "").split(",")] if arguments.get("countries") else None
            max_age_days = int(arguments.get("max_age_days", "7"))
            
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"""Search AI/ML jobs in India:

Parameters:
- Technologies: {', '.join(technologies) if technologies else 'Greenhouse (default)'}
- Countries: {', '.join(countries) if countries else 'IN (default)'}
- Max Age: {max_age_days} days

Profile: {COMPACT_USER_PROFILE.name} with 4+ years in AI/ML, NLP, LLMs
Skills: {', '.join(COMPACT_USER_PROFILE.skills)}

Use search-jobs tool to find matching positions."""
                        )
                    )
                ]
            )

        if name == "job-application":
            job_id = int(arguments.get("job_id", "0"))
            custom_message = arguments.get("custom_message", "")
            
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"""Create application for job ID: {job_id}

Profile: AI/ML Engineer, 4+ years experience
Skills: {', '.join(COMPACT_USER_PROFILE.skills)}
Custom message: {custom_message if custom_message else 'None'}

Use get-job-details and analyze-job-match tools to create tailored application."""
                        )
                    )
                ]
            )

        raise ValueError("Prompt implementation not found")

    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        return [
            Tool(
                name="search-jobs",
                description="Search AI/ML jobs (saves full data to JSON, returns compact summary)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "technologies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Company slugs (defaults to ['greenhouse'])",
                        },
                        "countries": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "Country codes (defaults to ['IN'])",
                        },
                        "max_age_days": {
                            "type": "integer",
                            "description": "Max age in days (default: 7)",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="get-job-details",
                description="Get compact job details from cache",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "integer",
                            "description": "Job ID",
                        },
                    },
                    "required": ["job_id"],
                },
            ),
            Tool(
                name="analyze-job-match",
                description="Analyze job-profile match",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "job_id": {
                            "type": "integer",
                            "description": "Job ID to analyze",
                        },
                    },
                    "required": ["job_id"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: Dict | None
    ) -> List[types.TextContent]:
        if name == "search-jobs":
            technologies = arguments.get("technologies")
            countries = arguments.get("countries")
            max_age_days = arguments.get("max_age_days", 7)
            
            results = await job_api.search_jobs(
                technologies=technologies,
                countries=countries,
                max_age_days=max_age_days
            )
            
            return [types.TextContent(
                type="text", 
                text=json.dumps(results, indent=2, default=str)
            )]
            
        elif name == "get-job-details":
            job_id = arguments.get("job_id")
            if not job_id:
                raise ValueError("Missing job_id")
                
            cached_job = job_api.get_cached_job(job_id)
            if cached_job:
                # Return compact version
                compact_details = {
                    "id": cached_job.id,
                    "title": cached_job.job_title,
                    "company": cached_job.company.get("name", "Unknown"),
                    "location": cached_job.location,
                    "remote": cached_job.remote,
                    "hybrid": cached_job.hybrid,
                    "salary": cached_job.salary_string,
                    "seniority": cached_job.seniority,
                    "description": cached_job.description[:1000] + "..." if len(cached_job.description) > 1000 else cached_job.description,
                    "url": cached_job.url
                }
                return [types.TextContent(
                    type="text",
                    text=json.dumps(compact_details, indent=2)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Job {job_id} not found in cache. Search first."
                )]
        
        elif name == "analyze-job-match":
            job_id = arguments.get("job_id")
            if not job_id:
                raise ValueError("Missing job_id")
                
            cached_job = job_api.get_cached_job(job_id)
            if not cached_job:
                return [types.TextContent(
                    type="text",
                    text=f"Job {job_id} not found in cache."
                )]
            
            # Quick skill matching
            user_skills = set(skill.lower() for skill in COMPACT_USER_PROFILE.skills)
            job_text = (cached_job.job_title + " " + cached_job.description).lower()
            
            matching_skills = [skill for skill in user_skills if skill in job_text]
            match_score = len(matching_skills) / len(user_skills) * 100
            
            analysis = {
                "job_id": job_id,
                "title": cached_job.job_title,
                "company": cached_job.company.get("name", "Unknown"),
                "match_score": round(match_score, 1),
                "matching_skills": matching_skills,
                "recommendation": "Strong Match" if match_score > 40 else "Good Match" if match_score > 20 else "Consider",
                "salary": cached_job.salary_string,
                "location": cached_job.location,
                "remote": cached_job.remote
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(analysis, indent=2)
            )]
            
        else:
            raise ValueError(f"Unknown tool: {name}")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jobstack",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Optimized JobStack API MCP Server')
    parser.add_argument('--api-config',
                       required=True,
                       help='Path to API configuration file')
    
    args = parser.parse_args()
    asyncio.run(main(args.api_config))