import re
import io
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

class DynamicMarkdownToPPTXService:
    """
    Service dinamis untuk convert Markdown ke PPTX
    - Auto detect template (pakai template jika ada, generate baru jika tidak)
    - Customizable font styling per header level
    - Support matplotlib code execution
    """
    
    def __init__(self, template_path=None, style_config=None):
        """
        Initialize service
        
        Args:
            template_path: Path ke template .pptx (optional)
            style_config: Dict untuk custom font styling (optional)
        """
        self.template_path = template_path
        self.use_template = False
        
        # Check template
        if template_path and Path(template_path).exists():
            self.prs = Presentation(template_path)
            self.use_template = True
            print(f"✅ Mode: Template-based (using {template_path})")
        else:
            self.prs = Presentation()
            self.prs.slide_width = Inches(10)
            self.prs.slide_height = Inches(5.625)
            print(f"✅ Mode: Generate from scratch")
            if template_path:
                print(f"   ⚠️  Template not found: {template_path}")
        
        # Set style configuration dengan merge
        self.style_config = self.get_default_style()
        if style_config:
            self._merge_style(style_config)
        
        self.code_blocks = {}
    
    def get_default_style(self):
        """
        Default styling configuration
        Bisa di-override saat init atau via set_style()
        """
        return {
            'h1': {  # Main title (# Header)
                'font_size': 44,
                'font_name': 'Calibri',
                'font_color': RGBColor(0, 51, 102),  # Navy blue
                'bold': True,
                'italic': False,
            },
            'h2': {  # Subtitle/Section heading (## Header)
                'font_size': 32,
                'font_name': 'Calibri',
                'font_color': RGBColor(230, 126, 34),  # Orange
                'bold': True,
                'italic': False,
            },
            'h3': {  # Sub-section heading (### Header)
                'font_size': 24,
                'font_name': 'Calibri',
                'font_color': RGBColor(52, 73, 94),  # Dark gray-blue
                'bold': True,
                'italic': False,
            },
            'body': {  # Regular text
                'font_size': 14,
                'font_name': 'Calibri',
                'font_color': RGBColor(60, 60, 60),
                'bold': False,
                'italic': False,
            },
            'bullet': {  # Bullet points
                'font_size': 16,
                'font_name': 'Calibri',
                'font_color': RGBColor(60, 60, 60),
                'bold': False,
                'italic': False,
            },
            'code': {  # Code blocks
                'font_size': 12,
                'font_name': 'Consolas',
                'font_color': RGBColor(100, 100, 100),
                'bold': False,
                'italic': False,
            }
        }
    
    def _merge_style(self, new_style):
        """
        Deep merge new style dengan existing style
        
        Args:
            new_style: Dict dengan style baru
        """
        for key, value in new_style.items():
            if key in self.style_config:
                # Update existing key
                self.style_config[key].update(value)
            else:
                # Add new key
                self.style_config[key] = value
    
    def set_style(self, style_dict):
        """
        Update style configuration
        
        Args:
            style_dict: Dict dengan format seperti get_default_style()
        
        Example:
            service.set_style({
                'h1': {
                    'font_size': 48,
                    'font_color': RGBColor(255, 0, 0),
                    'bold': True
                }
            })
        """
        self._merge_style(style_dict)
        print(f"✅ Style updated for: {', '.join(style_dict.keys())}")
    
    def apply_text_style(self, paragraph, style_type='body'):
        """
        Apply styling ke paragraph berdasarkan style type
        
        Args:
            paragraph: Paragraph object dari text frame
            style_type: Key dari style_config ('h1', 'h2', 'h3', 'body', 'bullet', 'code')
        """
        # Get style dengan fallback ke body
        if style_type in self.style_config:
            style = self.style_config[style_type]
        else:
            style = self.style_config.get('body', {})
        
        # Apply style properties yang ada
        if 'font_size' in style and style['font_size']:
            paragraph.font.size = Pt(style['font_size'])
        if 'font_name' in style and style['font_name']:
            paragraph.font.name = style['font_name']
        if 'font_color' in style and style['font_color']:
            paragraph.font.color.rgb = style['font_color']
        if 'bold' in style:
            paragraph.font.bold = style['bold']
        if 'italic' in style:
            paragraph.font.italic = style['italic']
    
    def extract_code_blocks(self, text):
        """Extract Python code blocks dari markdown"""
        code_pattern = r'``````'
        matches = re.findall(code_pattern, text, re.DOTALL)
        
        modified_text = text
        for i, code in enumerate(matches):
            placeholder = f'[[[CODE_BLOCK_{i}]]]'
            self.code_blocks[placeholder] = code
            modified_text = modified_text.replace(
                f'``````', 
                placeholder, 
                1
            )
        
        return modified_text
    
    def execute_code_block(self, code):
        """Execute Python code dan return matplotlib image"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            namespace = {'plt': plt, 'np': np}
            
            plt.clf()
            plt.close('all')
            exec(code, namespace)
            
            if plt.get_fignums():
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                plt.close('all')
                return ('image', buffer)
            else:
                return ('error', 'No plot generated')
                
        except ImportError:
            return ('skip', 'matplotlib not installed')
        except Exception as e:
            return ('error', str(e))
    
    def create_blank_slide(self):
        """Create blank slide"""
        if self.use_template:
            # Gunakan blank layout dari template
            try:
                blank_layout = self.prs.slide_layouts[6]
            except IndexError:
                blank_layout = self.prs.slide_layouts[-1]
            
            slide = self.prs.slides.add_slide(blank_layout)
        else:
            # Create blank dari scratch
            blank_layout = self.prs.slide_layouts[6]
            slide = self.prs.slides.add_slide(blank_layout)
            
            # Remove all shapes
            for shape in list(slide.shapes):
                sp = shape.element
                sp.getparent().remove(sp)
            
            # Set background
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor(255, 255, 255)
        
        return slide
    
    def add_styled_textbox(self, slide, text, left, top, width, height, style_type='body'):
        """
        Add textbox dengan custom styling
        
        Args:
            slide: Slide object
            text: Text content
            left, top, width, height: Position dan size dalam inches
            style_type: Style type ('h1', 'h2', 'h3', 'body', 'bullet')
        """
        textbox = slide.shapes.add_textbox(
            Inches(left), 
            Inches(top), 
            Inches(width), 
            Inches(height)
        )
        
        text_frame = textbox.text_frame
        text_frame.word_wrap = True
        text_frame.clear()
        
        p = text_frame.add_paragraph()
        p.text = text
        p.alignment = PP_ALIGN.LEFT
        
        self.apply_text_style(p, style_type)
        
        return textbox
    
    def add_bullet_textbox(self, slide, bullets, left, top, width, style_type='bullet'):
        """
        Add textbox dengan bullet points
        
        Args:
            slide: Slide object
            bullets: List of bullet texts
            left, top, width: Position dan size
            style_type: Style type (default 'bullet')
        
        Returns:
            Total height yang dipakai
        """
        total_height = len(bullets) * 0.35 + 0.2
        
        textbox = slide.shapes.add_textbox(
            Inches(left),
            Inches(top),
            Inches(width),
            Inches(total_height)
        )
        
        text_frame = textbox.text_frame
        text_frame.word_wrap = True
        text_frame.clear()
        
        for bullet_text in bullets:
            p = text_frame.add_paragraph()
            p.text = bullet_text
            p.level = 0
            self.apply_text_style(p, style_type)
        
        return total_height
    
    def fill_template_placeholder(self, slide, title=None, content=None):
        """
        Fill placeholder di template slide
        
        Args:
            slide: Slide object
            title: Title text
            content: Content text atau list
        """
        for shape in slide.placeholders:
            ph_type = shape.placeholder_format.type
            
            # Title placeholder
            if ph_type == 1 and title:
                shape.text = title
                # Apply h2 style ke title
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        if paragraph.text:  # Only apply if has text
                            self.apply_text_style(paragraph, 'h2')
            
            # Body/Content placeholder
            elif ph_type in [2, 7] and content:
                if not shape.has_text_frame:
                    continue
                
                text_frame = shape.text_frame
                text_frame.clear()
                
                if isinstance(content, list):
                    for item in content:
                        p = text_frame.add_paragraph()
                        p.text = str(item)
                        p.level = 0
                        self.apply_text_style(p, 'bullet')
                else:
                    p = text_frame.add_paragraph()
                    p.text = str(content)
                    self.apply_text_style(p, 'body')
    
    def add_slide_from_content(self, title=None, content=None, image_buffer=None, 
                               image_path=None, layout_index=1):
        """
        Add slide dengan content
        Mode auto: template-based atau generated
        
        Args:
            title: Slide title
            content: String atau list untuk content
            image_buffer: Matplotlib image buffer
            image_path: Path ke image file
            layout_index: Layout index jika pakai template
        """
        if self.use_template:
            # Mode template: gunakan layout dan fill placeholder
            try:
                layout = self.prs.slide_layouts[layout_index]
            except IndexError:
                layout = self.prs.slide_layouts[1]
            
            slide = self.prs.slides.add_slide(layout)
            self.fill_template_placeholder(slide, title, content)
        
        else:
            # Mode generate: buat manual dengan positioning
            slide = self.create_blank_slide()
            
            current_y = 0.5
            
            # Add title
            if title:
                self.add_styled_textbox(slide, title, 0.5, current_y, 9, 0.8, 'h2')
                current_y += 1
            
            # Add content
            if content:
                if isinstance(content, list):
                    height = self.add_bullet_textbox(slide, content, 0.8, current_y, 8.5, 'bullet')
                    current_y += height + 0.3
                else:
                    self.add_styled_textbox(slide, content, 0.5, current_y, 9, 0.6, 'body')
                    current_y += 0.8
        
        # Add image (both modes)
        if image_buffer or image_path:
            try:
                left = Inches(1.5)
                top = Inches(3 if self.use_template else current_y) # type: ignore
                width = Inches(7)
                
                if image_buffer:
                    slide.shapes.add_picture(image_buffer, left, top, width=width)
                elif image_path and Path(image_path).exists():
                    slide.shapes.add_picture(image_path, left, top, width=width)
            except Exception as e:
                print(f"⚠️  Error adding image: {e}")
        
        return slide
    
    def convert_markdown(self, md_content, output_path):
        """
        Convert markdown ke PPTX
        
        Args:
            md_content: String markdown content
            output_path: Output file path
        """
        # Extract code blocks
        md_content = self.extract_code_blocks(md_content)
        
        # Split by slide separator
        slides_content = md_content.split('\n---\n')
        
        for idx, slide_content in enumerate(slides_content):
            if not slide_content.strip():
                continue
            
            lines = [l for l in slide_content.split('\n') if l.strip()]
            
            title = None
            content_items = []
            image_buffer = None
            image_path_found = None
            
            for line in lines:
                line = line.strip()
                
                # Header level 1 (# Header)
                if line.startswith('# '):
                    title = line.replace('# ', '').strip()
                
                # Header level 2 (## Header)
                elif line.startswith('## '):
                    heading = line.replace('## ', '').strip()
                    if not title:
                        title = heading
                    else:
                        content_items.append(heading)
                
                # Header level 3 (### Header)
                elif line.startswith('### '):
                    content_items.append(line.replace('### ', '').strip())
                
                # Bullet point
                elif line.startswith('* ') or line.startswith('- '):
                    bullet_text = line.lstrip('*- ').strip()
                    content_items.append(bullet_text)
                
                # Image reference
                elif line.startswith('!['):
                    match = re.match(r'!\[.*?\]\((.*?)\)', line)
                    if match:
                        image_path_found = match.group(1)
                
                # Code block
                elif '[[[CODE_BLOCK_' in line:
                    match = re.search(r'\[\[\[CODE_BLOCK_(\d+)\]\]\]', line)
                    if match:
                        code_key = f'[[[CODE_BLOCK_{match.group(1)}]]]'
                        code = self.code_blocks.get(code_key, '')
                        
                        result_type, result_data = self.execute_code_block(code)
                        
                        if result_type == 'image':
                            image_buffer = result_data
                        elif result_type == 'error':
                            content_items.append(f"⚠️ {result_data}")
                
                # Regular text
                elif line:
                    content_items.append(line)
            
            # Add slide
            content = content_items if content_items else None
            self.add_slide_from_content(
                title=title,
                content=content,
                image_buffer=image_buffer,
                image_path=image_path_found,
                layout_index=1
            )
        
        # Save
        self.prs.save(output_path)
        mode = "template-based" if self.use_template else "generated"
        print(f"\n✅ Presentasi berhasil dibuat ({mode}): {output_path}")
        print(f"   Total slides: {len(self.prs.slides)}")
    
    def save(self, output_path):
        """Save presentation"""
        self.prs.save(output_path)
        print(f"✅ Saved: {output_path}")


# # ============ CONTOH PENGGUNAAN ============

# def example_with_template():
#     """Contoh pakai template"""
    
#     # Custom font styling (hanya override yang perlu)
#     custom_style = {
#         'h1': {
#             'font_size': 48,
#             'font_name': 'Arial',
#             'font_color': RGBColor(255, 0, 0),  # Red
#             'bold': True,
#         },
#         'h2': {
#             'font_size': 36,
#             'font_color': RGBColor(0, 102, 204),  # Blue
#             'bold': True,
#         },
#         'bullet': {
#             'font_size': 18,
#         }
#     }
    
#     service = DynamicMarkdownToPPTXService(
#         template_path='data/ppt/template.pptx',
#         style_config=custom_style
#     )
    
#     markdown_content = """
# # Judul Utama

# ---

# ## Topik 1

# * Poin pertama
# * Poin kedua
# * Poin ketiga

# ---

# ## Topik 2 - Data

# import matplotlib.pyplot as plt
# import numpy as np

# x = np.linspace(0, 10, 100)
# y = np.sin(x)

# plt.figure(figsize=(10, 5))
# plt.plot(x, y, linewidth=2)
# plt.title('Sine Wave')
# plt.grid(True, alpha=0.3)
# plt.tight_layout()
# """
#     service.convert_markdown(markdown_content, 'output_template.pptx')
    
    
# def example_without_template():
#     """Contoh tanpa template"""
    
#     service = DynamicMarkdownToPPTXService(
#         template_path=None  # Tidak pakai template
#     )
    
#     markdown_content = """
# # Welcome

# ---

# ## Introduction

# * Feature 1
# * Feature 2
# * Feature 3
# """
    
#     service.convert_markdown(markdown_content, 'output_generated.pptx')


# # if __name__ == '__main__':
#     # example_with_template()
#     # example_without_template()