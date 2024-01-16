from moviepy.editor import VideoFileClip
from pydub.utils import make_chunks
from pydub import AudioSegment
from tkinter import filedialog, messagebox
from tkinter import ttk
import tkinter as tk
import threading
import whisper
import queue
import os

class App:

    def __init__(self, master):

        self.chunk_name = "chunk.wav"
        self.AUDIO_ORIGINAL = ''
        self.AUDIO = ''
        self.FILE = ''

        self.master = master
        self.master.title("Transcription app")
        self.frame = tk.Frame(self.master)
        self.frame.grid()

        top_frame = tk.Frame(self.frame)
        top_frame.grid(row=0, column=0)

        left_frame = tk.Frame(top_frame)
        left_frame.grid(row=0, column=0)

        right_frame = tk.Frame(top_frame)
        right_frame.grid(row=0, column=1)

        bot_frame = tk.Frame(self.frame)
        bot_frame.grid(row=1, column=0, columnspan=2)

        self.audio_button = tk.Button(left_frame, text="Seleccionar archivo de Audio", command = self.get_audio)
        self.audio_button.grid(pady=(20,0), padx=(20,0))

        self.audio_info = tk.Button(right_frame, width=25, state='disabled', bd=0)
        self.audio_info.grid(pady=(20,0), padx=(10,20))

        self.file_button = tk.Button(left_frame, text="Seleccionar archivo de salida", command = self.get_file)
        self.file_button.grid(pady=10, padx=(20,0))

        self.file_info = tk.Button(right_frame, width=25, state='disabled',bd=0)
        self.file_info.grid(pady=10, padx=(10,20))

        self.start_button = tk.Button(bot_frame, width=25, text="Iniciar transcripcion", command = self.loading)
        self.start_button.grid(pady=(20,50))

        self.progressbar = ttk.Progressbar(bot_frame, orient=tk.HORIZONTAL, length=200, mode='determinate', maximum=100)
        self.progressbar['value'] = 0

        self.text_button = tk.Button(bot_frame, width=44, state='disabled', bd=0, 
        text='Este proceso dura aproximadamente \nla mitad de la duración del audio.\nPor favor, Espere...')

        self.end_button = tk.Button(bot_frame, text="Proceso Finalizado.\nCerrar", command = self.quit)

        self.master.protocol("WM_DELETE_WINDOW", self.quit)

        self.task_queue = queue.Queue()
        


    def thread_complete(self):
        if not self.task_queue.empty():
            self.task_queue.get().join()
            self.master.after(0, self.thread_complete)
        else:
            thread = threading.Thread(target = self.start)
            self.task_queue.put(thread)
            self.task_queue.get().start()

    def get_audio(self):
        thread = threading.Thread(target = self.do_get_audio)
        self.task_queue.put(thread)
        self.task_queue.get().start()
        
    def get_file(self):
        thread = threading.Thread(target = self.do_get_file)
        self.task_queue.put(thread)
        self.task_queue.get().start()
            
    def do_get_audio(self):
        file = filedialog.askopenfile(title='Seleccionar audio', filetypes=[
            ('Audio files', '*.mp3'),('Audio files', '*.wav'),
            ('Audio files', '*.ogg'),('Audio files', '*.mp4')])
        if file is not None:
            self.AUDIO = self.convert(file.name)
            self.audio_info.config(width=0, text=self.AUDIO_ORIGINAL)

    def do_get_file(self):
        file = filedialog.askopenfile(title='Seleccionar archivo de salida')
        if file is not None:
            self.FILE = file.name
            self.file_info.config(width=0, text=self.FILE)

    def loading(self):
        if self.AUDIO == '' and self.FILE == '':
            messagebox.showinfo('ChoseFiles' ,'Por favor, selecciona los archivos de entrada y salida.')
        else:
            self.start_button.grid_forget()
            self.file_button.config(state='disabled')
            self.audio_button.config(state='disabled')
            messagebox.showinfo('EveryTime' ,
                '''    Este programa requiere 2GB de Ram.
Por favor tengalo en cuenta antes de realizar
otras tareas con este equipo durante el proceso''')
            self.progressbar.grid(pady=(20, 5))
            self.text_button.grid(pady=(0,10))
            self.progressbar.step(2)
            self.thread_complete()
            
    def start(self):
        model = whisper.load_model("small.pt")
        model.language = "Spanish"
        
        myaudio = AudioSegment.from_file(self.AUDIO, "wav") 

        chunk_length_ms = 300000 #5min
        chunks = make_chunks(myaudio, chunk_length_ms)

        for i, chunk in enumerate(chunks):

            chunk.export(self.chunk_name, format="wav")
            result = model.transcribe(self.chunk_name)
            timeStamp = str((i*5)//60).zfill(2) + ':' + str((i*5)%60).zfill(2)

            with open(self.FILE, 'a', encoding="utf-8") as f:
                f.write('\nminuto '+timeStamp+'\n')
                f.write(result["text"])

            self.progressbar['value']+=100/len(chunks)
            self.master.update_idletasks()

        self.end()

    def end(self):
        self.progressbar.grid_forget()
        self.text_button.grid_forget()
        self.end_button.pack(pady=(20))

    def quit(self):
        os.remove(self.chunk_name)
        if not self.AUDIO == self.AUDIO_ORIGINAL:
            os.remove(self.AUDIO)
        self.master.destroy()
    
    def convert(self, ruta):
        self.AUDIO_ORIGINAL = ruta
        archivo = AudioSegment.from_file(ruta)
        nombre, extension = os.path.splitext(ruta)

        if extension == '.wav':
            return ruta
        
        elif extension == '.mp4':                     
            video = VideoFileClip(ruta)               
            audio = video.audio                       
            audio.write_audiofile(nombre+'.wav')
            return nombre+'.wav'
        
        else:
            return archivo.export(nombre+'.wav', format = 'wav').name

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
