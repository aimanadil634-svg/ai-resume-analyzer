"""
Curated skills database organized by category.
Used for keyword-based extraction from resumes and job descriptions.
"""

SKILLS_DB = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "matlab", "perl", "dart", "objective-c", "sql", "bash", "shell"
    ],
    "Web Development": [
        "html", "css", "react", "react.js", "angular", "vue", "vue.js",
        "node.js", "nodejs", "express", "django", "flask", "fastapi",
        "spring", "spring boot", "next.js", "nuxt.js", "redux", "graphql",
        "rest api", "restful api", "webpack", "tailwind", "bootstrap",
        "jquery", "sass", "less"
    ],
    "Data Science & ML": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "data analysis",
        "data visualization", "statistics", "regression", "classification",
        "clustering", "neural networks", "cnn", "rnn", "lstm", "transformers",
        "llm", "large language models", "generative ai", "data mining",
        "feature engineering", "model deployment", "mlops", "opencv"
    ],
    "Databases": [
        "mysql", "postgresql", "mongodb", "sqlite", "redis", "oracle",
        "sql server", "cassandra", "dynamodb", "elasticsearch", "firebase",
        "neo4j", "mariadb"
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
        "jenkins", "ci/cd", "terraform", "ansible", "git", "github",
        "gitlab", "bitbucket", "linux", "nginx", "microservices",
        "serverless", "lambda", "cloudformation", "helm"
    ],
    "Business & Soft Skills": [
        "leadership", "communication", "teamwork", "project management",
        "agile", "scrum", "kanban", "problem solving", "critical thinking",
        "time management", "stakeholder management", "negotiation",
        "presentation", "collaboration", "mentoring", "decision making",
        "adaptability", "strategic planning"
    ],
    "Tools & Platforms": [
        "jira", "confluence", "slack", "trello", "figma", "tableau",
        "power bi", "excel", "salesforce", "sap", "photoshop",
        "illustrator", "vs code", "postman", "jupyter"
    ],
    "Marketing & Design": [
        "seo", "sem", "google analytics", "content marketing",
        "social media marketing", "email marketing", "branding",
        "ui/ux", "ui design", "ux design", "adobe creative suite",
        "copywriting", "market research"
    ],
}

# Flattened lookup for fast matching: skill -> category
ALL_SKILLS = {}
for category, skills in SKILLS_DB.items():
    for skill in skills:
        ALL_SKILLS[skill.lower()] = category

# Common action verbs that strengthen resume bullet points (used for suggestions)
STRONG_ACTION_VERBS = [
    "achieved", "built", "created", "designed", "developed", "drove",
    "engineered", "implemented", "improved", "increased", "launched",
    "led", "managed", "optimized", "reduced", "spearheaded", "streamlined",
    "transformed", "delivered", "automated", "architected", "scaled"
]

WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "duties included",
    "tasked with", "in charge of"
]

ATS_PROBLEM_SECTIONS = [
    "summary", "objective", "experience", "work experience", "education",
    "skills", "projects", "certifications"
]
