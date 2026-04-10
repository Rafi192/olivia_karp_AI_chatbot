# ingestion/schemas.py

COLLECTION_SCHEMAS = {

    "blogs": {
        "fields": [
            "title", "author", "category", "tags",
            "summary", "content", "status", "read_time"
        ],
        "required_fields": ["title", "content"],
        "template": """Blog Post:
        Title: {title}
        Author: {author}
        Category: {category}
        Tags: {tags}
        Read Time: {read_time}
        Status: {status}
        Summary: {summary}
        Content: {content}
        """
    },

    "courseideas": {
        "fields": [
            "title", "category", "skillLevel", "description",
            "keyTopics", "whoIsThisCourseFor", "yourName", "status"
        ],
        "required_fields": ["title", "description"],
        "template": """Course Idea:
        Title: {title}
        Category: {category}
        Skill Level: {skillLevel}
        Status: {status}
        Description: {description}
        Key Topics: {keyTopics}
        Who Is This For: {whoIsThisCourseFor}
        Submitted By: {yourName}
        """
    },

    "joinmentorcoaches": {
        "fields": [
            "mentorName", "expertise", "experienceYears",
            "preferredMode", "availability", "status"
        ],
        "required_fields": ["mentorName", "expertise"],
        "template": """Mentor / Coach Profile:
        Name: {mentorName}
        Expertise: {expertise}
        Experience: {experienceYears} years
        Preferred Mode: {preferredMode}
        Availability: {availability}
        Status: {status}
        """
    },

    "reviews": {
        "fields": [
            "reviewerName", "reviewFor", "reviewType",
            "rating", "comments", "status"
        ],
        "required_fields": ["reviewFor", "comments"],
        "template": """Review:
        Reviewer: {reviewerName}
        Reviewed For: {reviewFor}
        Type: {reviewType}
        Rating: {rating} / 5
        Status: {status}
        Comments: {comments}
        """
    },

    "media": {
        "fields": [
            "title", "mediaType", "fileUrl",
            "uploadedBy", "tags", "description", "status"
        ],
        "required_fields": ["title", "description"],
        "metadata_fields": ["fileUrl", "thumbnailUrl"],
        "template": """Media:
        Title: {title}
        Type: {mediaType}
        Uploaded By: {uploadedBy}
        Tags: {tags}
        Status: {status}
        Description: {description}
        File URL: {fileUrl}
        Thumbnail URL: {thumbnailUrl}
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
        "metadata_fields": ["companyURL", "companyLogo"],
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

    "applyjobs": {
        "fields": [
            "jobId", "userId", "coverLetter",
            "portfolioUrl", "linkedinUrl", "status"
        ],
        "required_fields": ["jobId", "userId"],
        "metadata_fields": ["portfolioUrl", "linkedinUrl"],
        "template": """Job Application:
        Job ID: {jobId}
        Applicant ID: {userId}
        Cover Letter: {coverLetter}
        Portfolio: {portfolioUrl}
        LinkedIn: {linkedinUrl}
        Status: {status}
        """
    },
    "courses": {
    "fields": [
        "title",
        "category",
        "level",
        "price",              
        "currency",           
        "description",
        "lessonsCount",
        "totalDuration",
        "skills",
        "tags"
    ],
    "required_fields": ["title", "description", "price"],

    "template": """Course:
Title: {title}
Category: {category}
Level: {level}
Price: {price} {currency}

Description:
{description}

Skills:
{skills}
"""
},

    "events": {
        "fields": [
            "title", "category", "eventType", "location", "mode",
            "description", "date", "endDate", "registrationDeadline",
            "capacity", "registeredCount", "isPaid", "price",
            "organizerName", "organizerEmail", "status"
        ],
        "required_fields": ["title", "description", "date"],
        "template": """Event:
        Title: {title}
        Category: {category}
        Type: {eventType}
        Location: {location}
        Mode: {mode}
        Status: {status}
        Date: {date}
        End Date: {endDate}
        Registration Deadline: {registrationDeadline}
        Capacity: {capacity}
        Registered: {registeredCount}
        Is Paid: {isPaid}
        Price: {price}
        Organizer: {organizerName}
        Organizer Email: {organizerEmail}
        Description: {description}
        """
    },
    "subscriptionplans": {
        "fields": [
            "title", "description", "price", "billingType",
            "features", "hasTrial", "trialDays",
            "isHighlighted", "status", "order"
        ],
        "required_fields": ["title", "description"],
        "template": """Subscription Plan:
        Title: {title}
        Description: {description}
        Price: {price}
        Billing Type: {billingType}
        Features: {features}
        Has Trial: {hasTrial}
        Trial Days: {trialDays}
        Highlighted: {isHighlighted}
        Status: {status}
        Order: {order}
        """
    }


}

# Collections to exclude from RAG entirely
EXCLUDED_COLLECTIONS = [
    "users",
    "notifications",
    "bookings",
    "contacts",
    "referrals",
]


CASUAL_PATTERNS = [
    "hello", "hi", "hey", "how are you", "how can you help",
    "what can you do", "who are you", "good morning", "good evening",
    "thanks", "thank you", "bye", "goodbye", "how can you assist me", "what can you do for me", "how are you"
]

def is_casual_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(pattern in query_lower for pattern in CASUAL_PATTERNS)