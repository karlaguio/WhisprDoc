#improt libraries
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

