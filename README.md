---

# INFO-5940 Assignment 1

---
# Step 1: Follow the TA github instructions to setup the INFO-5940 environment.

## 🚀 Setup Guide  
### 1️⃣ Clone the Repository  

Open a terminal and run:  

```bash
git clone https://github.com/Zuoooooo/INFO5940-Assignment-1.git
```

open this folder's(INFO5940-Assignment-1) terminal

---

### 2️⃣ Configure OpenAI API Key  

Since `docker-compose.yml` expects environment variables, follow these steps:  

#### ➤ Option 1: Set the API Key in `.env` (Recommended)  

1. Inside the project folder, create a `.env` file:  

   ```bash
   touch .env
   ```

2. Add the class API key and base URL:  

   ```plaintext
   OPENAI_API_KEY=your-api-key-here
   OPENAI_BASE_URL=https://api.ai.it.cornell.edu/
   TZ=America/New_York
   ```

3. Modify `docker-compose.yml` to include this `.env` file:  

   ```yaml
   version: '3.8'
   services:
     devcontainer:
       container_name: info-5940-devcontainer
       build:
         dockerfile: Dockerfile
         target: devcontainer
       environment:
         - OPENAI_API_KEY=${OPENAI_API_KEY}
         - OPENAI_BASE_URL=${OPENAI_BASE_URL}
         - TZ=${TZ}
       volumes:
         - '$HOME/.aws:/root/.aws'
         - '.:/workspace'
       env_file:
         - .env
   ```

4. Restart the container:  

   ```bash
   docker-compose up --build
   ```

Now, API key will be automatically loaded inside the container.  

---
# Step 2: 

After that, open docker and select "images" run "file name" -- info5940-assignment-1

# Step 3: 

Return to VScode, press shift+command+p, select: Dev Containers: Rebuild and Reopen in Container

Select From 'docker-compose.yml' and then directly click 'OK'

# Step 4: Install the reuired Library

1. pip install pdfminer.six

Now you can see there is no underline on the top library list and make sure the library is a new version.

# Step 5 Run the application

In the terminal, navigate to the directory containing chatbot.py, then run:

- streamlit run assignmentchatbot.py

Open any link you want, and right now you can test

