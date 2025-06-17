# WhisprDoc – AI Notetaker for Medical Consultations

WhisprDoc is an AI assistant for doctors that transcribes and summarizes patient consultations so physicians can focus on human connection rather than note-taking.

### Description

In modern medicine, physicians often spend a significant portion of patient consultations focused on a computer screen, typing notes into an Electronic Health Record (EHR). This can detract from the crucial human element of the doctor-patient relationship.

**Doctor's AI Scribe** is a prototype desktop application that addresses this problem. It actively listens to the conversation between a doctor and a patient, transcribes it using **OpenAI's Whisper**, and then uses **Google's Gemini API** to generate a structured, professional clinical summary (in SOAP note format). This frees the doctor to maintain eye contact, listen actively, and build better rapport with their patient.

This repository contains a proof-of-concept application with a clean user interface and a dual-API pipeline. It's built to be easily adapted with your personal API keys.

### Features

* **Simple User Interface**: A clean, intuitive GUI built with Python's native `Tkinter` library.
* **One-Click Recording**: A large "Start/Stop" button to easily manage the recording process.
* **Real-Time Audio Capture**: Uses the `sounddevice` library to record high-quality audio from the system's microphone.
* **Dual AI-Powered Workflow**:
    * **Transcription**: Utilizes **OpenAI's Whisper** for fast and accurate speech-to-text conversion.
    * **Summarization**: Leverages **Google's Gemini Pro** to intelligently summarize the transcription into a structured SOAP note.
* **Easy Export**: A "Copy to Clipboard" function allows for seamless pasting of the generated summary into any EHR system.
* **Extensible by Design**: Heavily commented code shows exactly where to plug in real API keys.

### How It Works

The application follows a simple, powerful pipeline:

1.  **Record**: The user clicks "Start Recording." The app captures audio from the microphone until "Stop Recording" is clicked.
2.  **Transcribe**: The recorded audio is sent to OpenAI's Whisper API. The application displays the raw, word-for-word transcription.
3.  **Summarize**: The complete transcription is then sent to the Google Gemini API with a prompt instructing it to create a clinical summary.
4.  **Display**: The final, structured SOAP note is displayed in a separate panel, ready for review and use.

### Requirements

To run this application, you will need Python 3 and the following libraries:

* `sounddevice`: For capturing audio from the microphone.
* `scipy`: Required by `sounddevice` for writing audio data to a `.wav` file.
* `numpy`: For handling the audio data array.
* `openai`: For accessing the Whisper API.
* `google-generativeai`: For accessing the Gemini API.

 ### Disclaimer

This is a proof-of-concept application and is **not intended for real clinical use in its current state**. Any use of this tool in a healthcare setting must comply with all privacy regulations (e.g., HIPAA) and professional standards. The generated output should always be reviewed and validated by a qualified medical professional before being entered into a patient's record.

