from jinja2 import Environment, FileSystemLoader
import os

class TemplateLoader:
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def get_template(self, template_type: str):
        template_name = f"{template_type}.html"
        return self.env.get_template(template_name) 