COLLECTION_SCHEMAS = {

    "applyjobs": {
        "fields": ["jobId", "userId", "coverLetter", "portfolioUrl", "linkedinUrl", "status"],
        "required_fields": ["jobId", "userId"],
        "template": """Job Application:
        Job ID: {jobId}
        Applicant ID: {userId}
        Cover Letter: {coverLetter}
        Portfolio: {portfolioUrl}
        LinkedIn: {linkedinUrl}
        Status: {status}
        """
    },

    "blogs": {
        "fields": ["blog_heading", "blog_body", "blog_summary"],
        "required_fields": ["blog_heading", "blog_body"],
        "template": """Blog Post:
        Heading: {blog_heading}
        Summary: {blog_summary}
        Content: {blog_body}
        """
    },

    "jobs": {
        "fields": [
            "title", "category", "jobType", "location",
            "description", "responsibility", "requirement",
            "skill", "companyName", "companyURL", "status",
            "hiredCount", "totalHiredCount"
        ],
        "required_fields": ["title", "description", "companyName"],
        "template": """Job Listing:
        Title: {title}
        Company: {companyName}
        Company URL: {companyURL}
        Category: {category}
        Job Type: {jobType}
        Location: {location}
        Status: {status}
        Skills Required: {skill}
        Description: {description}
        Responsibilities: {responsibility}
        Requirements: {requirement}
        Hired: {hiredCount} / {totalHiredCount}
        """
    },

}