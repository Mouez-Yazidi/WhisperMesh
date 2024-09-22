# WhisperMesh 🌐🔊
WhisperMesh is your cutting-edge chatbot that seamlessly blends voice and text interactions, creating a rich, intuitive conversational experience. With the power of LLM models and a sophisticated vector database, WhisperMesh understands your needs like never before, providing tailored responses that resonate with your queries.

Harnessing the RAG framework from Haystack, our app excels in extracting relevant information, ensuring that every interaction is not only engaging but also data-driven. Whether you prefer speaking or typing, WhisperMesh adapts to your style, transforming your input into insightful answers with a personal touch.

Join the conversation with WhisperMesh, where your voice matters, and let us guide you through a world of knowledge and discovery! 🌟💬✨

# 🚀 Getting Started
### Prerequisites
* Python 3.11 or above 🐍
* Groq API for inference, which is currently available for free in its beta version with rate limits. You can obtain your API key here after creating an account: [Groq API](https://medium.com/r/?url=https%3A%2F%2Fconsole.groq.com%2Fkeys).
* Additionally, you have the option to use Qdrant either locally or via Qdrant Cloud. Its API is also free to use. Access it here: [Qdrant Cloud](https://medium.com/r/?url=https%3A%2F%2Fcloud.qdrant.io%2Flogin).
* For embeddings, you can use the Cohere API. It offers a free tier and you can sign up and get your API key here: [Cohere API](https://medium.com/r/?url=https%3A%2F%2Fcohere.ai).
# 💻 Local Deployment
### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/my-streamlit-app.git
cd my-streamlit-app
```
### 2. Install Dependencies
Navigate to the local directory and install the necessary dependencies:
```bash
cd local
pip install -r requirements.txt
```
### 3. Running the App Locally
To run the app locally, execute the following command:

```bash
streamlit run ../app/main.py --config config.toml
```
You should now be able to access the app at http://localhost:8501 🌐.

### 🐳 Optional: Running with Docker
If you prefer running the app in a Docker container, follow these steps:
1. Make sure you have Docker installed 🐋.
2. Build the Docker image:
```bash
docker build -t my-streamlit-app .
```
3. Run the container:
```bash
docker run -p 8501:8501 my-streamlit-app
```
# ☁️ Streamlit Cloud Deployment
### 1. Prepare Your Repository
Ensure that your code is pushed to a GitHub repository 📂.

### 2. Link with Streamlit Cloud
* Visit Streamlit Cloud and sign in.
* Connect your GitHub repository 🔗.
* Choose your repository and branch.
### 3. Streamlit Cloud Configuration
Your *cloud/setup.sh* and *cloud/config.toml* will be used by Streamlit Cloud automatically to set up the environment.

Streamlit Cloud will:
* Install dependencies from cloud/requirements.txt 📦
* Use cloud/config.toml for configuration ⚙️
### 4. Environment Variables
Add any sensitive information (API keys, secrets) to the cloud/secrets.toml file. For example:

```csharp
[api_keys]
example_api_key = "your-api-key"
```
🎉 You’re all set! Your app will now be live on Streamlit Cloud!

# 🌟 Features
* Configurable: Separate configuration files for local and cloud deployment.
* Docker Support: Deploy the app using Docker for local containerization.

# 🤝 Contributing
We welcome contributions! Please see our CONTRIBUTING.md for guidelines.

# 📄 License
This project is licensed under the MIT License. See the LICENSE file for more details.

# 📧 Contact
If you have any questions or suggestions, feel free to open an issue or contact us at mouez.yazidi2016@gmail.com.
