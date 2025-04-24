import tkinter as tk
import requests

from tkinter import ttk, filedialog, messagebox 

from threading import Thread
import re
import os


class ParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Telegram Parser')
        self.root.geometry('600x400')

        self.parsing = False
        self.stop_parsing = False
        self.create_widgets()
        self.setup_layout()

    def brouse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[('Text files', '*.txt')])
        if file_path:
            self.file_path_var.set(file_path)

    def start_parsing(self):
        file_path = self.file_path_var.get()
        save_folder = self.folder_path_var.get()


        if not file_path:
            messagebox.showerror('Error', 'Укажите файл с каналами Telegram')
            return
        try:
            with open(file_path,'r', encoding='utf-8') as f:
                channels = []
                for line in f.readlines():
                    channels.append(line.strip())
        except Exception as e:
            print(e)
            return
        if not channels:
            messagebox.showerror('Error', 'Файл не содержит каналов для парсинга')
            return
        self.parsing = True
        self.stop_parsing = False
        self.stop_btn.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.DISABLED)
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set(0)

        Thread(target=self.parse_channels, args=(channels, save_folder), daemon=True).start()

    def parse_channels(self, channels, save_folder):
        total_channels = len(channels)
        for i, channel in enumerate(channels):
            if self.stop_parsing:
                break
            self.log_message(f'Парсинг канала: {channel}')
            self.progress_var.set(((i + 1) / total_channels) * 100)
            try:
                response = requests.get(channel)
            except requests.RequestException as e:
                self.log_message(f'шибка при загрузке канала {channel}: {e}')
                continue
            image_links = self.extract_image_links(response.text)
            if not  image_links:
                self.log_message(f'В канале {channel} не найдено изображений')
                continue
            self.log_message(f'Найдено {len(image_links)} изображений')
            channel_name = channel.split('/')[-1]
            channel_folder = os.path.join(save_folder, channel_name)
            os.makedirs(channel_folder, exist_ok=True)

            total_images = len(image_links)
            for j, img_url in enumerate(image_links):
                if self.stop_parsing:
                    break
                self.download_image(img_url, channel_folder)

    def download_image(self, url, channel_folder):
        origin_filename = url.split('/')[-1].split('?')[0]
        safe_filename = self.sanitize_filename(origin_filename)
        if not safe_filename:
            safe_filename = 'image.jpg'
        save_path = os.path.join(channel_folder, safe_filename)


        if os.path.exists(save_path):
            self.log_message(f'Файл уже существует: {safe_filename} ')
            return save_path
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                if self.stop_parsing:
                    return None
                file.write(chunk)
        self.log_message(f'Сохранено: {safe_filename}')
        return save_path



    def sanitize_filename(self, filename):
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        max_length = 100
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext
        return filename






    def extract_image_links(self, response):
        pattern = r'https?://[^\s]+?\.(?:jpg|jpeg|png|gif|bmp|webp)(?:\?[^\s]*)?'
        image_links =  re.findall(pattern, response)
        return image_links


    def log_message(self, message):
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.root.update()


    def stop_parsing(self):
        pass

    def log_text_yview(self):
        pass

    def brouse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path_var.set(folder_path)

    def create_widgets(self):
        self.file_frame = ttk.LabelFrame(self.root, text='Файл с каналами Telegram')
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(self.file_frame, textvariable=self.file_path_var, width=50)
        self.browse_btn = ttk.Button(self.file_frame, text='Обзор...', command=self.brouse_file)

        self.settings_frame = ttk.LabelFrame(self.root, text='Настройки')
        self.folder_path_var = tk.StringVar(value='downloads')
        self.folder_entry = ttk.Entry(self.settings_frame, textvariable=self.folder_path_var, width=50)
        self.folder_browse_btn = ttk.Button(self.settings_frame, text='Обзор...', command=self.brouse_folder)


        self.control_frame = ttk.Frame(self.root)
        self.start_btn = ttk.Button(self.control_frame, text='Start', command=self.start_parsing)
        self.stop_btn = ttk.Button(self.control_frame, text='Stop', command=self.stop_parsing, state=tk.DISABLED)

        self.log_frame = ttk.LabelFrame(self.root, text='Лог выполнения')
        self.log_text = tk.Text(self.log_frame, height=10, wrap=tk.WORD)
        self.log_scroll = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text_yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)


        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100, mode='determinate')

    def setup_layout(self):
        self.file_frame.pack(pady=5, padx=5, fill=tk.X)
        self.file_entry.pack(pady=5, padx=5,side=tk.LEFT, fill=tk.X, expand=True)
        self.browse_btn.pack(pady=5, padx=5, side=tk.RIGHT)

        self.settings_frame.pack(pady=5, padx=5, fill=tk.X)
        self.folder_entry.pack(side=tk.LEFT, pady=5, padx=5, fill=tk.X, expand=True)
        self.folder_browse_btn.pack(side=tk.RIGHT, pady=5, padx=5)


        self.control_frame.pack(pady=5, padx=5, expand=True, fill=tk.BOTH)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack(side=tk.RIGHT, padx=5)

        self.log_frame.pack(pady=5,padx=5,expand=True, fill=tk.BOTH)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.progress_bar.pack(pady=5, padx=5, fill=tk.X)



root = tk.Tk()
p = ParserApp(root)

root.mainloop()