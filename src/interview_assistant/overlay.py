import tkinter as tk


def show_overlay(text):
    root = tk.Tk()
    root.title('Interview Assistant')
    root.attributes('-topmost', True)
    root.geometry('500x400+100+100')
    root.resizable(True, True)

    text_widget = tk.Text(root, wrap='word', font=('Arial', 10))
    text_widget.insert('1.0', text)
    text_widget.pack(fill='both', expand=True, padx=10, pady=10)

    root.mainloop()


def generate_html(text):
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Interview Assistant</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        pre {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>Interview Assistant</h1>
    <pre>{text}</pre>
</body>
</html>"""