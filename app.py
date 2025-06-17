#Improt libraries
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import os
import time

# Need these for the AI
import openai
import google.generativeai as genai

# Main app class
class MedicalScribeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Doctor's AI Scribe")
        self.root.geometry("800x700")
        self.root.configure(bg="#f1f5f9")

        # --- SPACE FOR API Keys ---
        # I wont add to the public repo my API keys for security, but they will be here
        self.openai_api_key = "OPENAI_API_KEY"
        self.gemini_api_key = "GEMINI_API_KEY"

        # App state variables
        self.is_recording = False
        self.audio_filename = "consultation_audio.wav"
        self.audio_data = []

        # Configure the AI clients right away
        if self.openai_api_key != "YOUR_OPENAI_API_KEY":
            openai.api_key = self.openai_api_key
        
        if self.gemini_api_key != "YOUR_GEMINI_API_KEY":
            genai.configure(api_key=self.gemini_api_key)

        # Build the UI
        self._setup_ui()

    def _setup_ui(self):
        # Setting up the main UI components
        main_frame = tk.Frame(self.root, bg="#f1f5f9", padx=25, pady=25)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # App Title
        title_label = tk.Label(main_frame, text="Doctor's AI Scribe", font=("Helvetica", 20, "bold"), bg="#f1f5f9", fg="#1e293b")
        title_label.pack(pady=(0, 10))
        
        # Status display to let the user know what's happening
        self.status_label = tk.Label(main_frame, text="Ready to record. Press 'Start' to begin.", font=("Helvetica", 11), bg="#f1f5f9", fg="#64748b")
        self.status_label.pack(pady=(0, 20))

        # The big red button
        self.record_button = tk.Button(main_frame, text="Start Recording", command=self.toggle_recording, font=("Helvetica", 14, "bold"), bg="#22c55e", fg="white", activebackground="#16a34a", width=20, relief=tk.FLAT, pady=8, borderwidth=0, highlightthickness=0)
        self.record_button.pack(pady=10)
        
        # This lets the user resize the text areas
        paned_window = tk.PanedWindow(main_frame, orient=tk.VERTICAL, bg="#f1f5f9", sashwidth=8, sashrelief=tk.RAISED)
        paned_window.pack(expand=True, fill=tk.BOTH, pady=10)

        # Area for the raw transcription
        transcription_frame = tk.Frame(paned_window, bg="#f1f5f9")
        transcription_label = tk.Label(transcription_frame, text="Live Transcription", font=("Helvetica", 12, "bold"), bg="#f1f5f9", fg="#1e293b")
        transcription_label.pack(pady=(5, 5), anchor="w")
        self.transcription_text = scrolledtext.ScrolledText(transcription_frame, wrap=tk.WORD, height=10, font=("Helvetica", 10), relief=tk.SOLID, borderwidth=1, state='disabled', bg="white")
        self.transcription_text.pack(expand=True, fill=tk.BOTH)
        paned_window.add(transcription_frame, minsize=100)

        # Area for the final summary
        summary_frame = tk.Frame(paned_window, bg="#f1f5f9")
        summary_label = tk.Label(summary_frame, text="AI Generated Clinical Summary (SOAP Note)", font=("Helvetica", 12, "bold"), bg="#f1f5f9", fg="#1e293b")
        summary_label.pack(pady=(5, 5), anchor="w")
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, height=15, font=("Helvetica", 10), relief=tk.SOLID, borderwidth=1, state='disabled', bg="white")
        self.summary_text.pack(expand=True, fill=tk.BOTH)
        paned_window.add(summary_frame, minsize=150)

        # Bottom section for buttons and stuff
        bottom_frame = tk.Frame(main_frame, bg="#f1f5f9")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        self.copy_button = tk.Button(bottom_frame, text="Copy Summary", command=self.copy_summary, font=("Helvetica", 10), state='disabled', relief=tk.FLAT, bg="#e2e8f0", fg="#334155")
        self.copy_button.pack(side=tk.LEFT, padx=(0, 10))

        # A little disclaimer so nobody gets any funny ideas
        disclaimer = tk.Label(bottom_frame, text="Disclaimer: This tool is for assistance only. It does not replace professional medical judgment or documentation standards.", font=("Helvetica", 8, "italic"), bg="#f1f5f9", fg="#94a3b8", wraplength=600, justify=tk.LEFT)
        disclaimer.pack(side=tk.RIGHT)
        
    def toggle_recording(self):
        # Flip between starting and stopping the recording
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.is_recording = True
        self.record_button.config(text="Stop Recording", bg="#ef4444", activebackground="#dc2626")
        self.status_label.config(text="Status: Recording audio...")
        self.audio_data = [] # Clear out any old recordings

        # Wipe the text boxes for the new session
        self._update_text_widget(self.transcription_text, "")
        self._update_text_widget(self.summary_text, "")
        self.copy_button.config(state='disabled')

        # Run the recording in a separate thread so the UI doesn't freeze
        self.recording_thread = threading.Thread(target=self._record_audio_stream)
        self.recording_thread.daemon = True
        self.recording_thread.start()

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False # This signals the recording thread to stop
            self.record_button.config(text="Start Recording", bg="#22c55e", activebackground="#16a34a")
            self.status_label.config(text="Status: Recording stopped. Processing...")
            self.record_button.config(state='disabled') # Don't let user click again while we process
            print("Recording stopped.")

    def _record_audio_stream(self):
        # Standard audio settings for speech-to-text
        samplerate = 16000
        channels = 1
        
        try:
            # This context manager handles the microphone stream
            with sd.InputStream(samplerate=samplerate, channels=channels, callback=self._audio_callback):
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            # Something went wrong with the mic
            messagebox.showerror("Audio Error", f"Could not start recording. Check microphone.\n\nError: {e}")
            self.root.after(0, self.reset_ui_after_error)
            return

        # Once the loop is done, save the file and kick off the AI stuff
        self._save_and_process_audio()

    def _audio_callback(self, indata, frames, time, status):
        # sounddevice calls this function for each chunk of audio
        if status:
            print(status)
        self.audio_data.append(indata.copy())

    def _save_and_process_audio(self):
        # If the user just clicked start/stop really fast
        if not self.audio_data:
            print("No audio was recorded.")
            self.status_label.config(text="Status: No audio recorded. Ready.")
            self.record_button.config(state='normal')
            return

        # Stitch all the audio chunks together and write to a WAV file
        recording = np.concatenate(self.audio_data, axis=0)
        write(self.audio_filename, 16000, recording)
        print(f"Recording saved to {self.audio_filename}")
        
        # Now, start the AI pipeline in another thread
        processing_thread = threading.Thread(target=self._run_ai_pipeline)
        processing_thread.daemon = True
        processing_thread.start()

    def _run_ai_pipeline(self):
        # This is where the AI happens
        
        # Quick check to make sure the user added their keys
        if self.openai_api_key == "YOUR_OPENAI_API_KEY" or self.gemini_api_key == "YOUR_GEMINI_API_KEY":
            self.root.after(0, messagebox.showerror, "API Key Error", "Please replace the placeholder API keys in the code before running.")
            self.root.after(0, self.reset_ui_after_error)
            return

        try:
            # Okay, time to call Whisper for the transcription
            self.root.after(0, self._update_status, "Status: Transcribing audio...")
            client = openai.OpenAI(api_key=self.openai_api_key)
            with open(self.audio_filename, "rb") as audio_file:
                transcription_result = client.audio.transcriptions.create(
                  model="whisper-1", 
                  file=audio_file
                )
                transcription = transcription_result.text
            self.root.after(0, self._update_text_widget, self.transcription_text, transcription)

            # Now, let's send the text to Gemini for the summary
            self.root.after(0, self._update_status, "Status: Generating clinical summary...")
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"""Summarize the following patient consultation into a structured clinical SOAP note.
            Ensure the output is professional, accurate, and ready for an Electronic Health Record.
            Transcript:
            ---
            {transcription}
            ---
            """
            response = model.generate_content(prompt)
            summary = response.text
            self.root.after(0, self._update_text_widget, self.summary_text, summary)

            # All done!
            self.root.after(0, self._update_status, "Status: Processing complete. Ready.")
            self.root.after(0, self.copy_button.config, {'state': 'normal'})

        except Exception as e:
            # if tehre is an error
            print(f"An error occurred during AI processing: {e}")
            self.root.after(0, messagebox.showerror, "Processing Error", f"An error occurred: {e}\n\nPlease check your API keys and network connection.")
            self.root.after(0, self.reset_ui_after_error)
        
        finally:
            # Always re-enable the button and delete the temp audio file
            self.root.after(0, self.record_button.config, {'state': 'normal'})
            if os.path.exists(self.audio_filename):
                os.remove(self.audio_filename)

    def _update_status(self, text):
        # A safe way to update the UI from a thread
        self.status_label.config(text=text)

    def _update_text_widget(self, widget, text):
        # A safe way to update text boxes from a thread
        widget.config(state='normal')
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, text)
        widget.config(state='disabled')
        
    def copy_summary(self):
        # Simple copy to clipboard
        self.root.clipboard_clear()
        summary_content = self.summary_text.get(1.0, tk.END)
        self.root.clipboard_append(summary_content)
        messagebox.showinfo("Copied", "The clinical summary has been copied to your clipboard.")
        
    def reset_ui_after_error(self):
        # Puts the UI back to a working state if something fails
        self.is_recording = False
        self.record_button.config(text="Start Recording", bg="#22c55e", activebackground="#16a34a", state='normal')
        self.status_label.config(text="Status: An error occurred. Please try again.")

def main():
    # Before we even start, let's make sure the user has the right libraries installed
    try:
        import sounddevice
        import scipy
        import openai
        import google.generativeai
    except ImportError:
        print("-----------------------------------------------------------")
        print("ERROR: Missing required libraries.")
        print("Please install them by running this command in your terminal:")
        print("pip install sounddevice scipy numpy openai google-generativeai")
        print("-----------------------------------------------------------")
        return

    # Let's get this show on the road
    root = tk.Tk()
    app = MedicalScribeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
