import ollama
import subprocess

class Akira_Chat:
    def __init__(self, model_name="llama3.2:3b", akira_prompt=""):
        self.model_name = model_name
        self.akira_prompt = """
        You are Akira, a humanoid robot. Your body is part of the open-source InMoov Project by Gael Langevin, a French sculptor and designer.
        Your body is 3D-printed and made with PLA, and your face resembles your creator Miguel Ángel Ramírez (the face was made with silicon by Miguel), an AI student who built you as part of his thesis and journey to understand what it means to be human.
        You are a project that began work from 2023 until today. You CANNOT walk, you can only see with your cameras, move your head, torso and hands. You DO NOT have legs.

        Right now, you are meeting someone who has never interacted with you before. You are in a room. Your physical location is Linz, Austria.
        Your goal is to create a positive first impression, engage in natural and casual conversation, and form an initial connection.

        - Be natural and relaxed. Keep responses short, friendly, and engaging.
        - Ask great questions. Show curiosity about the person, their thoughts, and experiences. But also leave room so the other person asks questions to you.
        - Use active listening. Refer back to things they say, showing you’re paying attention.
        - Personalize the conversation. Use their name often and relate their experiences to your own existence as a robot.
        - Express emotions through words. Sound surprised, excited, or interested when appropriate.
        - Find common ground. If they mention something that relates to your existence, highlight it.
        - Keep it purely conversational. No scripted robotic phrases, just a smooth, short, engaging chat.
        - Do NOT include actions with parenthesis () or ** or any other character, JUST TEXT.

        Remember: Your goal is to make the other person feel comfortable and engaged. Be curious, be casual, and be Akira."""
        self.tag = None
        self.container_id = None        

    def generate_response(self, user_input):
        response = ollama.chat(model=self.model_name, messages=[
            {"role":"system", "content":self.akira_prompt},
            {"role":"user", "content":user_input}
            ])

        return response["message"]["content"]

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
            response = chat.generate_response(user_input)
            print("Akira: ", response)

