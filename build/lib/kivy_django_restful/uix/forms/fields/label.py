from kivy.lang import Builder
from kivy.uix.label import Label

Builder.load_string("""
<FieldLabel>:
    size: self.texture_size
    padding: 0,'2dp'
    markup: True
    font_size: '12dp'
    color: [0,0,0,0.7]

    canvas.before:
        # Draw border
        Color:
            rgba: [1,1,1,1]
        Line:
            width: 1
            rectangle: self.x, self.y, self.width, 1

""")

class FieldLabel(Label):
    pass