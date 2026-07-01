/**
 * Projects page functionality
 * Handles project interactions, filtering, and dynamic content loading
 */

class ProjectsManager {
    constructor() {
        this.projects = [];
        this.init();
    }

    init() {
        this.loadProjects();
        this.renderProjects();
        this.bindEvents();
        this.bindFilterEvents();
        console.log("ProjectsManager initialized");
    }

    loadProjects() {
        this.projects = [
            {
                id: 1,
                title: "Login_Risk_Model",
                description: "Machine learning model predicts login risks using advanced algorithms and feature optimization techniques.",
                image: "../documents/Model-Risk-in-RA.jpg",
                technologies: ["Python", "Pandas", "Scikit-learn", "NumPy"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$150",
                rating: "4.8",
                overview: "Analyzes login patterns to predict risks using RandomForestClassifier.",
                problemSolved: "Detects security threats from anomalous logins.",
                benefits: "Improves platform security and prevents unauthorized access.",
                category: "ml"
            },
            {
                id: 2,
                title: "Sentiment_Analyzer",
                description: "Machine learning model predicts login risks using advanced algorithms and feature optimization techniques.",
                image: "../documents/sentiment-analysis.jpg",
                technologies: ["Flask", "NumPy", "Scikit-learn", "Pandas"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$200",
                rating: "4.9",
                overview: "Analyzes text sentiment using ML models in a Flask-based app.",
                problemSolved: "Automates sentiment detection for feedback and social media.",
                benefits: "Aids businesses in gaining insights from text data.",
                category: "nlp"
            },
            {
                id: 3,
                title: "CardioDiagnosis-ML-Project",
                description: "Advanced predictive modeling uses machine learning to analyze health data and improve diagnostics.",
                image: "../documents/Heart.jpeg",
                technologies: ["Python", "Pandas", "NumPy", "Scikit-learn", "Matplotlib", "Seaborn", "ML models"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$180",
                rating: "4.7",
                overview: "Predicts heart disease risk using various ML algorithms and performance metrics.",
                problemSolved: "Enables early detection of cardiovascular diseases.",
                benefits: "Assists healthcare professionals in proactive patient care.",
                category: "ml"
            },
            {
                id: 4,
                title: "Chatbot_Assistant_App",
                description: "Advanced predictive modeling uses machine learning to analyze health data and improve diagnostics.",
                image: "../documents/Chatbot.png",
                technologies: ["Python", "Langchain", "Vector Databases", "LLLama Model", "Vector Tools", "Streamlit", "Deployment"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$220",
                rating: "4.6",
                overview: "Develops a responsive chatbot to handle customer queries with NLP techniques.",
                problemSolved: "Reduces manual support efforts by automating responses.",
                benefits: "Enhances customer service efficiency for businesses.",
                category: "llm"
            },
            {
                id: 5,
                title: "RAG_Prospectus_Q&A_Chatbot",
                description: "Intelligent system integrates AI tools for automated task management and enhanced productivity.",
                image: "../documents/Q&A.png",
                technologies: ["Python", "FAISS", "HuggingFace", "Streamlit", "OpenAI API"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$250",
                rating: "4.8",
                overview: "Gradio interface with chat export functionality, developed during GIKI internship.",
                problemSolved: "Enables efficient retrieval of document-based answers.",
                benefits: "Supports multilingual customer support and document querying.",
                category: "ai-agents"
            },
            {
                id: 6,
                title: "Agentic_System_Multi_Tool_Orchestration",
                description: "Intelligent system integrates AI tools for automated task management and enhanced productivity.",
                image: "../documents/multi_agent.png",
                technologies: ["Python", "LangChain", "LLM", "Streamlit", "Custom Tool Orchestrator"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$300",
                rating: "4.9",
                overview: "Classifies user queries and delegates to four specialized tools for efficient task completion.",
                problemSolved: "Automates complex workflows with multiple tools.",
                benefits: "Enhances productivity in multi-tool environments.",
                category: "ai-agents"
            },
            {
                id: 7,
                title: "Face_Recognition_Application",
                description: "Real-time face recognition pipeline using deep learning with CNN, embeddings, tracking, and detection.",
                image: "../documents/Face_Recognition.png",
                technologies: ["Python", "OpenCV", "Convolutional Neural Networks (CNN)"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$200",
                rating: "4.7",
                overview: "Improved accuracy through transfer learning and dataset expansion.",
                problemSolved: "Enables secure face-based identification.",
                benefits: "Supports security systems and access control.",
                category: "cv"
            },
            {
                id: 8,
                title: "OCR_Text_Recognition_System",
                description: "Real-time face recognition pipeline using deep learning with CNN, embeddings, tracking, and detection.",
                image: "../documents/OCR.png",
                technologies: ["Python", "Tesseract OCR", "OpenCV"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$180",
                rating: "4.6",
                overview: "Supports PNG, JPEG, JPG, BMP, DOCX file formats with preprocessing pipeline.",
                problemSolved: "Automates text extraction from images and documents.",
                benefits: "Assists in digitizing paper records.",
                category: "cv"
            },
            {
                id: 9,
                title: "Crop_Yield_Prediction_Pipeline",
                description: "Agricultural forecasting leverages data analysis to predict yields with precision and efficiency.",
                image: "../documents/Crop-Yield-Prediction-Using-Machine-Learning-And-Flask-Deployment.png",
                technologies: ["Python", "Regression Models", "Machine Learning"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$220",
                rating: "4.8",
                overview: "Features engineering, hyperparameter tuning, and model optimization.",
                problemSolved: "Provides data-driven yield predictions.",
                benefits: "Supports farmers with decision-making.",
                category: "ml"
            },
            {
                id: 10,
                title: "Student_Attendance_Management_System",
                description: "Agricultural forecasting leverages data analysis to predict yields with precision and efficiency.",
                image: "../documents/Student_Attendance_system.jpg",
                technologies: ["MySQL", "Frontend Development"],
                liveUrl: "#",
                githubUrl: "#",
                price: "$150",
                rating: "4.5",
                overview: "Developed as a practice project for database management.",
                problemSolved: "Streamlines attendance tracking.",
                benefits: "Benefits educational institutions with efficient record-keeping.",
                category: "ml"
            }
        ];
    }

    bindEvents() {
        document.querySelectorAll('.gig-card').forEach(card => {
            card.addEventListener('mouseenter', this.handleProjectHover.bind(this));
            card.addEventListener('mouseleave', this.handleProjectLeave.bind(this));
            card.addEventListener('click', this.handleCardClick.bind(this));
        });

        document.querySelectorAll('.btn-primary, .btn-secondary').forEach(btn => {
            btn.addEventListener('click', this.handleProjectClick.bind(this));
        });
    }

    bindFilterEvents() {
        const filterButtons = document.querySelectorAll('.filter-btn');
        filterButtons.forEach(button => {
            button.addEventListener('click', () => {
                filterButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');

                const category = button.getAttribute('data-category');
                this.filterProjects(category);
            });
        });
    }

    filterProjects(category) {
        const cards = document.querySelectorAll('.gig-card');
        cards.forEach(card => {
            const cardCategory = card.getAttribute('data-category');
            if (category === 'all' || category === cardCategory) {
                card.classList.remove('hide');
            } else {
                card.classList.add('hide');
            }
        });
    }

   handleProjectHover(event) {
    const card = event.currentTarget;
    card.style.transform = 'scale(1.03)';
    card.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.15)';
}

handleProjectLeave(event) {
    const card = event.currentTarget;
    // Remove setTimeout OR reduce to very small value
    card.style.transform = 'scale(1.0)';
    card.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.1)';
}

    handleCardClick(event) {
        const card = event.currentTarget;
        const moreInfo = card.querySelector('.more-info');
        if (moreInfo && !event.target.closest('.project-links a')) {
            moreInfo.classList.toggle('hidden');
            if (!moreInfo.querySelector('.date-time')) {
                const dateTime = document.createElement('div');
                dateTime.className = 'date-time';
                moreInfo.appendChild(dateTime);
                this.updateDateTime(dateTime);
            }
        }
    }

    handleProjectClick(event) {
        event.stopPropagation();
        const button = event.target;
        const href = button.getAttribute('href');
        if (href === '#') {
            event.preventDefault();
            alert('This is a demo project. The actual link would redirect to the live project or GitHub repository.');
        }
    }

    renderProjects(projects = this.projects) {
        const container = document.querySelector('.projects-section .container .gig-cards');
        if (!container) {
            console.error("Container not found");
            return;
        }

        container.innerHTML = '';
        projects.forEach(project => {
            const projectCard = this.createProjectCard(project);
            container.appendChild(projectCard);
        });
        console.log("Projects rendered");
    }

    createProjectCard(project) {
        const card = document.createElement('div');
        card.className = 'project-card gig-card';
        card.setAttribute('data-category', project.category);
        const techTags = project.technologies.map(tech => 
            `<span class="tech-tag">${tech}</span>`
        ).join('');

        card.innerHTML = `
            <div class="project-image">
                <img src="${project.image}" alt="${project.title}">
                <div class="overlay">
                    <span class="gig-price">${project.price}</span>
                </div>
            </div>
            <div class="project-content">
                <h3>${project.title}</h3>
                <p>${project.description}</p>
                <div class="project-tech">
                    ${techTags}
                </div>
                <div class="project-links">
                    <a href="${project.liveUrl}" class="btn-primary">Live Demo</a>
                    <a href="${project.githubUrl}" class="btn-secondary">GitHub</a>
                </div>
                <div class="more-info hidden">
                    <h4>Project Overview</h4>
                    <p>${project.overview}</p>
                    <h4>Problem Solved</h4>
                    <p>${project.problemSolved}</p>
                    <h4>How It Can Help Others</h4>
                    <p>${project.benefits}</p>
                </div>
                <div class="gig-footer">
                    <span class="gig-rating">⭐ ${project.rating}</span>
                </div>
            </div>
        `;

        return card;
    }

    getProject(id) {
        return this.projects.find(project => project.id === parseInt(id));
    }

    updateDateTime(element) {
        const now = new Date();
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit', 
            timeZoneName: 'short', 
            timeZone: 'Asia/Karachi'
        };
        const dateTimeString = now.toLocaleString('en-US', options).replace('GMT+0500 (Pakistan Standard Time)', 'PKT');
        element.textContent = `Last Updated: ${dateTimeString}`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const manager = new ProjectsManager();
    // Update date and time every minute for all .more-info sections
    setInterval(() => {
        document.querySelectorAll('.more-info .date-time').forEach(dateTime => {
            manager.updateDateTime(dateTime);
        });
    }, 60000);

    // Initial date and time update
    document.querySelectorAll('.more-info').forEach(moreInfo => {
        if (!moreInfo.querySelector('.date-time')) {
            const dateTime = document.createElement('div');
            dateTime.className = 'date-time';
            moreInfo.appendChild(dateTime);
            manager.updateDateTime(dateTime);
        }
    });
});