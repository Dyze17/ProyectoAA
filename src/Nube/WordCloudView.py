from wordcloud import WordCloud
import matplotlib.pyplot as plt

class WordCloudView:
    def __init__(self, frequency_map, width=800, height=600, background_color='white'):
        self.frequency_map = frequency_map
        self.width = width
        self.height = height
        self.background_color = background_color

    def draw(self):
        wc = WordCloud(width=self.width, height=self.height,
                       background_color=self.background_color).generate_from_frequencies(self.frequency_map)

        plt.figure(figsize=(self.width / 100, self.height / 100))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis("off")
        plt.show()
