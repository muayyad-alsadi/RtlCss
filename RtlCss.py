#! /usr/bin/python
"""
Rtl Override Css Generator by Muayyad Alsadi

Copyright (c) 2014 Vision Advanced Systems

Usage: RtlCss.py input1.css input2.css

nested blocks is supported because of things like this

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(359deg); }
}

"""

import sys
import re
from collections import OrderedDict


comment_re=re.compile('/\*.*?\*/', re.S | re.M)
css_token=re.compile('(?:\{|\}|;|[^{};]+)', re.S | re.M)
non_space=re.compile('(\S+)', re.S | re.M)
bg_pos_re=re.compile('((?:left|center|right|top|bottom|[\.\d]+(?:em|ex|px|in|cm|mm|pt|pc|%)?)\s+(?:left|center|right|top|bottom|[\.\d]+(?:em|ex|px|in|cm|mm|pt|pc|%)?))', re.S | re.M)
border_re=re.compile('''^((?:(?P<style>none|hidden|dotted|dashed|solid|double|groove|ridge|inset|outset|initial|inherit)|(?P<width>[\.\d]+(?:em|ex|px|in|cm|mm|pt|pc|%))|(?P<color>\S+))\s*)+$''', re.S | re.M)

def try_int(i):
    r=None
    try: r=int(i)
    finally: return r

def try_float(i):
    r=None
    try: r=float(i)
    finally: return r


def parse_four_sides(value):
    """return top, right, bottom, left"""
    a=non_space.findall(value)
    l=len(a)
    if l==1: return a[0], a[0], a[0], a[0]
    elif l==2: return a[0], a[1], a[0], a[1]
    elif l==3: return a[0], a[1], a[2], a[1]
    elif l==4: return a[0], a[1], a[2], a[3]
    else: return None, None, None, None

def parse_xpos_ypos(value):
    """
    background-position: xpos ypos;
    """
    a=non_space.findall(value)
    if len(a)==2: xpos,ypos=a
    else: xpos, ypos=None,None
    if xpos == 'top' or xpos == 'bottom' or ypos == 'right' or ypos == 'left': xpos, ypos=ypos, xpos
    return xpos, ypos


def get_bg_xpos_ypos(value):
    """
    background: color position/size repeat origin clip attachment image|initial|inherit;
    """
    a=bg_pos_re.findall(value)
    if len(a)<1: return None, None
    return parse_xpos_ypos(a[0])

def prase_border(value):
    width, style, color=None,None,None
    m=border_re.match('1px solid black')
    if m:
        width=m.group('width')
        style=m.group('style')
        color=m.group('color')
    return width, style, color

def flip_text(text):
    text=text.replace('&rsaquo;', '&bogo;').replace('&lsaquo;', '&rsaquo;').replace('&bogo;', '&lsaquo;')
    return text

class CssBlock(object):
    defaults={
        'left': 'auto', 'right': 'auto',
        'margin': '0', 'padding': '0',
        'margin-right': '0', 'padding-right': '0',
        'margin-left': '0', 'padding-left': '0',
        'outline': 'none', 'border': 'none',
        'outline-style':'none', 'border-style':'none',
        'outline-right': 'none', 'border-right': 'none', 
        'outline-left': 'none', 'border-left': 'none', 
        'outline-right-style':'none', 'border-right-style':'none',
        'outline-left-style':'none', 'border-left-style':'none',
        'outline-width':'medium', 'border-width':'medium',
        'outline-right-width':'medium', 'border-right-width':'medium',
        'outline-left-width':'medium', 'border-left-width':'medium',
        }
    def __init__(self, selector, rules=None):
        self.selector=selector
        self.rules=rules or []
    
    def __str__(self):
        return self.selector+'{' + \
           ';\n'.join(map(lambda r: str(r),self.rules)).replace('}\n;\n', '}\n') + '}\n'

    def normalize(self, recursive=True):
        self.selector=self.selector.strip()
        if recursive:
            for rule in self.rules: rule.normalize()
    
    def collect(self):
        k=OrderedDict()
        for rule in self.rules:
            if not isinstance(rule, CssStyle): continue
            k[rule.style]=rule.value
            for r in rule.expand(): k[r.style]=r.value
        return k

    def get_rtl_override(self):
        """This function can handle the following styles:
float: right;
clear: right;
text-algin: right
left: auto
right: 5px

margin-right: 1px;
margin: top right bottom left;
padding-right: 1px;
padding: top right bottom left;

border-right-style: solid;
border-right-width: 1px
border-right-color: #ccc
border-right: 1px solid #ccc;
border-style: top right bottom left;
border-width: top right bottom left;
border-color: top right bottom left;

background-position: xpos ypos;
background-position: xpos% ypos%;
background-position: right top;
background: color position/size repeat origin clip attachment image|initial|inherit;

outline*: same as border
        """
        done=set()
        overrides=[]
        collected=self.collect()
        for style, value in collected.iteritems():
            if style in done: continue
            done.add(style)
            prefix=''
            if style.startswith('*'):
               style=style[1:]
               prefix='*'
            elif style.startswith('-webkit-'):
               prefix='-webkit-'
               style=style[strlen(prefix):]
            elif style.startswith('-moz-'):
               prefix='-moz-'
               style=style[strlen(prefix):]
            if style=='content':
               new_value=flip_text(value)
               if new_value==value: continue
               overrides.append(CssStyle(prefix+style, new_value))
            elif style=='border-radius':
               # https://developer.mozilla.org/en-US/docs/Web/CSS/border-radius
               # TODO: we should expend it, this is just a quick optimistic solution
               a=non_space.findall(value)
               if len(a)==4:
                   overrides.append(CssStyle(prefix+style, '%s %s %s %s' % (a[1], a[0], a[3], a[2]) ))
            elif style=='background-position':
               xpos,ypos=parse_xpos_ypos(value)
               if xpos==None: continue
               if xpos=='left' or xpos=='right':
                   xpos='right' if xpos=='left' else 'left'
               elif xpos.endswith('%'):
                   v=try_float(xpos[:-1])
                   if xpos==None: continue
                   xpos=str(100-v)+'%'
                   if xpos=='50.0%': continue
               overrides.append(CssStyle(prefix+style, xpos+' '+ypos))
            elif (style=='clear' or style=='float' or style=='text-align') and \
               (value =='left' or value == 'right'):
               new_value='right' if value=='left' else 'left'
               overrides.append(CssStyle(prefix+style, new_value))
            elif style=='right' or style=='left':
                other_style=style.replace('right', 'bogoight').replace('left', 'right').replace('bogoight', 'left')
                done.add(prefix+other_style)
                value=collected.get(prefix+style, self.defaults[style])
                other_value=collected.get(prefix+other_style, self.defaults[style])
                if value==other_value: continue
                overrides.append(CssStyle(prefix+style, other_value))
                overrides.append(CssStyle(preifx+other_style, value))
            elif (style.endswith('-right') or style.endswith('-left')) and self.defaults.has_key(style):
                other_style=style.replace('-right', '-bogoight').replace('-left', '-right').replace('-bogoight', '-left')
                done.add(prefix+other_style)
                value=collected.get(prefix+style, self.defaults[style])
                other_value=collected.get(prefix+other_style, self.defaults[style])
                if value==other_value: continue
                overrides.append(CssStyle(prefix+style, other_value))
                overrides.append(CssStyle(prefix+other_style, value))
            
                
        for rule in filter(lambda r: isinstance(r, CssBlock), self.rules):
            block=rule.get_rtl_override()
            if block: overrides.append(block)
        if not overrides: return None
        return CssBlock(self.selector, overrides)

class CssStyle(object):
    s1=set(('margin', 'padding', 'border-style', 'border-color', 'border-width', 'outline-style', 'outline-color', 'outline-width',))
    def __init__(self, style, value):
        self.style=style
        self.value=value
    
    def normalize(self):
        self.style=self.style.strip()
        self.value=self.value.strip()
        self.value=self.value.rstrip(';')
        self.value=self.value.strip()
    
    def expand(self):
        style=self.style
        prefix=''
        if style.startswith('*'):
            # handle MSIE hack *margin
            prefix='*'
            style=style[1:]
        if style in self.s1:
            top, right, bottom, left = parse_four_sides(self.value)
            if top!=None: return [CssStyle(prefix+style+'-left', left), CssStyle(prefix+style+'-right', right)]
        elif style=='border':
            width, style, color = parse_border(self.value)
            a=[]
            if width:
                a.append(CssStyle(prefix+'border-left-width', width))
                a.append(CssStyle(prefix+'border-right-width', width))
            if style:
                a.append(CssStyle(prefix+'border-left-style', style))
                a.append(CssStyle(prefix+'border-right-style', style))
            if color:
                a.append(CssStyle(prefix+'border-left-color', color))
                a.append(CssStyle(prefix+'border-right-color', color))
            return a
        elif style=='background':
            xpos, ypos=get_bg_xpos_ypos(self.value)
            if xpos!=None: return [CssStyle(prefix+style+'-position', xpos+' '+ypos)]
        return []
    
    def __str__(self):
        return self.style+':'+self.value
def parse_css(css):
    css=comment_re.sub('', css)
    blocks=[]
    block=None
    last_token=None
    stack=[]
    for token in css_token.findall(css):
        if token=='{':
            block=CssBlock(last_token)
            if len(stack)==0: blocks.append(block)
            else: stack[-1].rules.append(block)
            stack.append(block)
        elif token=='}':
            block=stack.pop()
            if last_token and ':' in last_token:
                style, value=last_token.split(':', 1)
                block.rules.append(CssStyle(style.strip(), value.strip()))
                last_token=None
        elif token==';':
            if not last_token or ':' not in last_token: last_token==None; continue
            style, value=last_token.split(':', 1)
            block.rules.append(CssStyle(style.strip(), value.strip()))
            last_token=None
        else:
            token=token.strip()
            if not token: continue
            last_token=token
    return blocks


def override_file(input_file):
    output_file=input_file.replace('.min.', '.').replace('.css', '.rtl.css')
    blocks=parse_css(open(input_file, 'rt').read())
    for block in blocks: block.normalize()
    out=[]
    for block in blocks:
        override=block.get_rtl_override()
        if override: out.append(override)
    print ' saving [%s] ' % output_file,
    f=open(output_file, 'wt+')
    f.write('\n'.join(map(lambda b: str(b), out)).replace('\n}', '}').replace('}', '}\n').replace(';\n', ';'))
    f.close()

def main():
    for input_file in sys.argv[1:]:
        print "generating RTL override for [%s]: ... " % input_file,
        if '.rtl.' in input_file:
            print 'SKIPPED'
            continue
        print ' started ... ',
        override_file(input_file)
        print ' done'

main()
