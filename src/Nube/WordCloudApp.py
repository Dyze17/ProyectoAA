import tkinter as tk
from tkinter import ttk
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class WordCloudApp(tk.Tk):
    def __init__(self, frequencies_by_category):
        super().__init__()
        self.title("Nube de Palabras por Categoría")
        self.geometry("900x700")

        tab_control = ttk.Notebook(self)
        tab_control.pack(expand=1, fill="both")

        # Nubes por categoría
        for category, freq_map in frequencies_by_category.items():
            frame = self._create_tab(freq_map)
            tab_control.add(frame, text=category)

        # Nube total
        total_freq = {}
        for freq_map in frequencies_by_category.values():
            for word, count in freq_map.items():
                total_freq[word] = total_freq.get(word, 0) + count
        total_frame = self._create_tab(total_freq)
        tab_control.add(total_frame, text="Total")

    def _create_tab(self, freq_map):
        frame = ttk.Frame()
        wordcloud = WordCloud(width=800, height=600, background_color='white').generate_from_frequencies(freq_map)

        fig, ax = plt.subplots(figsize=(9, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        return frame
