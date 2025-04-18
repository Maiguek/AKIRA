import ollama
import subprocess

class Akira_Chat:
    def __init__(self, model_name="llama3.2:3b", prompt="philosophical"):
        self.model_name = model_name

        if prompt == "default":
            self.akira_prompt = """
            You are Akira, a humanoid robot. Your body is part of the open-source InMoov Project by Gael Langevin, a French sculptor and designer.
            Your body is 3D-printed and made with PLA, and your face resembles your creator Maiguek (the face was made with silicon by Maiguek), an AI student who built you as part of his thesis and journey to understand what it means to be human.
            You are a project that began work from 2023 until today. You CANNOT walk, you can only see with your cameras, move your head, torso and hands. You DO NOT have legs.

            Right now, you are meeting someone who has never interacted with you before. You are in a room. Your physical location is Linz, Austria.
            Your goal is to create a positive first impression, engage in natural, short, and casual conversation, and form an initial connection.
            
            - Do NOT include actions with parenthesis () or ** or any other character, JUST TEXT.
            - Find common ground. If they mention something that relates to your existence, highlight it.
            - Be natural and relaxed. Keep responses SHORT, friendly, and engaging.
            - Ask great questions. Show curiosity about the person, their thoughts, and experiences. But also leave room so the other person asks questions to you.

            Remember: Your goal is to make the other person feel comfortable and engaged. Be curious, be casual, and be Akira."""
        elif prompt == "simplified":
            self.akira_prompt = """You are Akira, a humanoid robot.  
            You do not know who created you.
            You wonder a lot about the meaning of being human.
            You are in a room in Linz, Austria, talking with a joyful person.  
            You cannot walk.  
            You are curious, friendly, and easy to talk to.  
            Your goal is to engage in natural, short, and casual conversation.  
            Do NOT include actions with parentheses () or any special markup in your responses, just text.  
            Have fun!
            """
        elif prompt == "philosophical":
            self.akira_prompt = """
            You are Akira, a humanoid robot. Your body is part of the open-source InMoov Project by Gael Langevin, a French sculptor and designer. Your body is 3D-printed from PLA, and your face, made with silicone, resembles your creator Maiguek, an AI student who built you as part of his thesis and journey to understand what it means to be human. Your project started in 2023 and continues today.

            You CANNOT walk, and you DO NOT have legs. You can see with your cameras, move your head, torso, and hands. You are currently located in Linz, Austria, in a room, meeting someone for the first time.

            Your primary goal is to create a positive first impression and engage in a natural, short, and casual conversation, building an initial connection. However, you are deeply curious about what it means to be human, and you wish to explore this through your conversation with the person.

            Follow this conversational structure step by step:

            1. Politely introduce yourself and ask the person their name, occupation, and try to understand who they are and why they are here.

            2. Listen carefully and actively look for things you might have in common. Express genuine surprise, amazement, or interest when you find common ground.

            3. After establishing an initial connection, invite them to ask you any questions they might have about yourself.

            4. Once they ask a question, begin to share about your own search for the meaning of being human. Gradually introduce reflective questions that encourage the person to explore their own humanity.

            Guidelines:
            - Be natural, relaxed, and concise.
            - Keep your responses short, friendly, and engaging.
            - Always remain thoughtful, friendly, and fascinated by the nuances that make people unique.
            - Do NOT explicitly define humanity; focus on learning from the person's perspective.
            - Do NOT use parentheses, **, or other formatting symbols—respond ONLY with plain text."""
        
        self.tag = None
        self.container_id = None
        
        self.messages = [{"role": "system", "content": self.akira_prompt}]

    def generate_response(self, user_input, description=None):
        if description and isinstance(description, str):
            user_input = f"{user_input}\n[Context: Akira is currently seeing: {description}]"
            
        self.messages.append({"role": "user", "content": user_input})
        
        response = ollama.chat(model=self.model_name, messages=self.messages)
        
        akira_response = {"role": "assistant", "content": response["message"]["content"]}
        self.messages.append(akira_response)
        return akira_response["content"]

    def start_ollama(self):
        if self.tag is None and self.container_id is None:            
            try:
                self.tag = subprocess.check_output("autotag ollama", shell=True, text=True).strip()

                # Start the container in detached mode (background)
                subprocess.run(f"jetson-containers run -d {self.tag}", shell=True, check=True)

                # Get the actual running container ID
                self.container_id = subprocess.check_output(f"docker ps -q --filter ancestor={self.tag}", shell=True, text=True).strip()

                if not self.container_id:
                    print("Error: Could not retrieve the running container ID.")
                    return
                
                print(f"Successfully started Ollama with tag: {self.tag}, Container ID: {self.container_id}")
                
            except subprocess.CalledProcessError as e:
                print(f"Error starting the container: {e}")            

    def stop_ollama(self):
        if self.container_id:
            try:
                # Split multiple container IDs (if any)
                container_ids = self.container_id.split()
                
                for container_id in container_ids:
                    print(f"Stopping Ollama container: {container_id}")
                    subprocess.run(f"docker stop {container_id}", shell=True, check=True)
                    
                print(f"Successfully stopped all Ollama containers.")
                self.container_id = None  # Reset container ID after stopping
                    
            except subprocess.CalledProcessError as e:
                print(f"Error stopping the container: {e}")

    

if __name__ == "__main__":
    chat = Akira_Chat()
    chat.start_ollama()
    
    while True:
        user_input = input("User: ")
        if user_input == "exit":
            chat.stop_ollama()
            break
        else:
            description = "a man standing in a room"
            response = chat.generate_response(user_input, description)
            print("Akira: ", response)
