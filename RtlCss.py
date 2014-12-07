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
import argparse

from collections import OrderedDict, defaultdict

comment_re=re.compile('/\*.*?\*/', re.S | re.M)
css_token=re.compile('(?:\{|\}|;|[^{};]+)', re.S | re.M)
non_space=re.compile('(\S+)', re.S | re.M)
bg_pos_re=re.compile('((?:left|center|right|top|bottom|[\.\d]+(?:em|ex|px|in|cm|mm|pt|pc|%)?)\s+(?:left|center|right|top|bottom|[\.\d]+(?:em|ex|px|in|cm|mm|pt|pc|%)?))', re.S | re.M)
border_re=re.compile('''^((?:(?P<style>none|hidden|dotted|dashed|solid|double|groove|ridge|inset|outset|initial|inherit)|(?P<width>[\.\d]+(?:em|ex|px|in|cm|mm|pt|pc|%)?)|(?P<color>\S+))\s*)+$''', re.S | re.M)
zero_re=re.compile('''\s*^0(\.0*)?\s*(?:em|ex|px|in|cm|mm|pt|pc|%)?\s*$''', re.S | re.M)

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

def parse_radius_4_sides(value):
    top_left, top_right, bottom_right, bottom_left = None, None, None, None
    a=non_space.findall(value)
    if len(a)==1:
        top_left, top_right, bottom_right, bottom_left = a[0], a[0], a[0], a[0]
    elif len(a)==2:
        top_left, top_right, bottom_right, bottom_left = a[0], a[1], a[0], a[1]
    elif len(a)==3:
        top_left, top_right, bottom_right, bottom_left = a[0], a[1], a[2], a[1]
    elif len(a)==4:
        top_left, top_right, bottom_right, bottom_left = a[0], a[1], a[2], a[3]
    return top_left, top_right, bottom_right, bottom_left



def parse_radius(value):
    """
    see https://developer.mozilla.org/en-US/docs/Web/CSS/border-radius
    """
    if '/' in value:
        horizontal, vertical = value.split('/',  1)
    else:
        horizontal, vertical = value, value
    corners=zip(parse_radius_4_sides(horizontal), 
        parse_radius_4_sides(vertical))
    if not corners[0] or corners[0][0]==None: return None, None, None, None
    top_left, top_right, bottom_right, bottom_left=map(lambda a: a[0]+' '+a[1] if a[0]!=a[1] else a[0], corners)
    return top_left, top_right, bottom_right, bottom_left
    

def parse_xpos_ypos(value):
    """
    background-position: xpos ypos;
    """
    a=non_space.findall(value)
    if len(a)==2: xpos,ypos=a
    else: xpos, ypos=None,None
    if xpos == 'top' or xpos == 'bottom' or ypos == 'right' or ypos == 'left': xpos, ypos=ypos, xpos
    if xpos!=None and (xpos == '0' or zero_re.match(xpos)): xpos='left'
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

# TODO: inherit from list
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
        'border-top-left-radius': '0', 'border-top-right-radius': '0',
        'border-bottom-right-radius': '0', 'border-bottom-left-radius': '0',
        }
    def __init__(self, selector, rules=None):
        self.selector=selector
        self.rules=[]
        self.clear()
        if rules: self.extend(rules)
    
    def clear(self):
        del self.rules[:]
        self._rules_set=set()

    def append(self, rule):
        h = str(rule)
        if h in self._rules_set: return
        self._rules_set.add(h)
        self.rules.append(rule)
    
    def extend(self, rules):
        for rule in rules: self.append(rule)
    
    def _render_body(self):
        return ';\n'.join(map(lambda r: str(r),self.rules)).replace('}\n;\n', '}\n')

    def __str__(self):
        return self.selector+'{' + self._render_body() + '}\n'

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

    def get_rtl_override(self, excludes=None):
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
        if excludes==None: excludes=defaultdict(list)
        done=set()
        overrides=[]
        collected=self.collect()
        blackstyles=excludes[self.selector]
        for style, value in collected.iteritems():
            if style in done: continue
            done.add(style)
            prefix=''
            if style.startswith('*'):
               style=style[1:]
               prefix='*'
            elif style.startswith('-webkit-'):
               prefix='-webkit-'
               style=style[len(prefix):]
            elif style.startswith('-moz-'):
               prefix='-moz-'
               style=style[len(prefix):]
            if style in blackstyles: continue
            if style=='content':
               new_value=flip_text(value)
               if new_value==value: continue
               overrides.append(CssStyle(prefix+style, new_value))
            elif style.startswith('border-') and style.endswith('-radius'):
               if 'border-radius' in blackstyles: continue
               # TODO: handle -moz-border-radius-bottomright, use and 'radius' in style
               if style=='border-radius': continue
               other_style=style.replace('-right', '-bogoight').replace('-left', '-right').replace('-bogoight', '-left')
               done.add(prefix+other_style)
               value=collected.get(prefix+style, self.defaults[style])
               other_value=collected.get(prefix+other_style, self.defaults[style])
               if value==other_value: continue
               overrides.append(CssStyle(prefix+style, other_value))
               overrides.append(CssStyle(prefix+other_style, value))
            elif style=='background-position':
               xpos,ypos=parse_xpos_ypos(value)
               if xpos==None: continue
               if xpos=='left' or xpos=='right':
                   xpos='right' if xpos=='left' else 'left'
               elif xpos.endswith('%'):
                   v=try_float(xpos[:-1])
                   if xpos==None: continue
                   xpos=str(100-v)+'%'
                   if zero_re.match(xpos): xpos='left'
                   elif xpos=='100.0%': xpos='right'
                   elif xpos=='50.0%': continue
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
                overrides.append(CssStyle(prefix+other_style, value))
            elif '-right' in style or '-left' in style:
                other_style=style.replace('-right', '-bogoight').replace('-left', '-right').replace('-bogoight', '-left')
                done.add(prefix+other_style)
                value=collected.get(prefix+style, self.defaults.get(style, None))
                other_value=collected.get(prefix+other_style, self.defaults.get(style, None))
                if value==other_value and collected.has_key(prefix+style) and collected.has_key(prefix+other_style): continue
                if other_value!=None: overrides.append(CssStyle(prefix+style, other_value))
                if value!=None: overrides.append(CssStyle(prefix+other_style, value))
            
                
        for rule in filter(lambda r: isinstance(r, CssBlock), self.rules):
            block=rule.get_rtl_override(excludes)
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
        elif style.startswith('-webkit-'):
            prefix='-webkit-'
            style=style[len(prefix):]
        elif style.startswith('-moz-'):
            prefix='-moz-'
            style=style[len(prefix):]
        if style in self.s1:
            top, right, bottom, left = parse_four_sides(self.value)
            if '-' in style: base,suffix=style.split('-',1); suffix="-"+suffix
            else: base,suffix=style, ''
            if top!=None: return [CssStyle(prefix+base+'-left'+suffix, left), CssStyle(prefix+base+'-right'+suffix, right)]
        elif style=='border-radius':
            top_left, top_right, bottom_right, bottom_left=parse_radius(self.value)
            if top_left!=None:
                return [
                    CssStyle(prefix+'border-top-left-radius', top_left),
                    CssStyle(prefix+'border-top-right-radius', top_right),
                    CssStyle(prefix+'border-bottom-right-radius', bottom_right),
                    CssStyle(prefix+'border-bottom-left-radius', bottom_left),
                  ]
        elif style=='border':
            width, style, color = prase_border(self.value)
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

class CssFile(CssBlock):
    def __init__(self, content=None, rules=None):
        super(CssFile, self).__init__('', rules)
        if content: self.parse(content)

    def __str__(self):
        return self._render_body()
    
    def get_rtl_override(self, excludes=None):
        if excludes==None: excludes=defaultdict(list)
        out=super(CssFile, self).get_rtl_override(excludes)
        return CssFile(rules=out.rules)

    def parse(self, css):
        css=comment_re.sub('', css)
        blocks=[]
        block=None
        last_token=None
        stack=[]
        for token in css_token.findall(css):
            if token=='{':
                block=CssBlock(last_token)
                if len(stack)==0: blocks.append(block)
                else: stack[-1].append(block)
                stack.append(block)
            elif token=='}':
                block=stack.pop()
                if last_token and ':' in last_token:
                    style, value=last_token.split(':', 1)
                    block.append(CssStyle(style.strip(), value.strip()))
                    last_token=None
            elif token==';':
                if not last_token or ':' not in last_token: last_token==None; continue
                style, value=last_token.split(':', 1)
                block.append(CssStyle(style.strip(), value.strip()))
                last_token=None
            else:
                token=token.strip()
                if not token: continue
                last_token=token
        self.clear()
        self.extend(blocks)
    
def override_file(input_file, excludes=None):
    if excludes==None: excludes=defaultdict(list)
    output_file=input_file.replace('.min.', '.').replace('.css', '.rtl.css')
    css=CssFile(open(input_file, 'rt').read())
    css.normalize()
    out=css.get_rtl_override(excludes)
    print ' saving [%s] ' % output_file,
    f=open(output_file, 'wt+')
    f.write(str(out).replace('\n}', '}').replace(';\n', ';'))
    f.close()

def main():
    parser = argparse.ArgumentParser(description='Generate RTL override CSS')
    parser.add_argument('-x', '--exclude', help='pass black list file, each line should be type:selector eg. border-radius:.btn')
    parser.add_argument('files', nargs='+')
    args = vars(parser.parse_args())
    exclude=args.get('exclude', None)
    excludes=defaultdict(list)
    if exclude:
        x=filter(lambda ll: len(ll)==2, map(lambda l: l.split(':', 1), open(exclude, 'rt').readlines()))
        for style, selector in x:
            excludes[selector.strip()].append(style.strip())
    for input_file in args['files']:
        print "generating RTL override for [%s]: ... " % input_file,
        if '.rtl.' in input_file:
            print 'SKIPPED'
            continue
        print ' started ... ',
        override_file(input_file, excludes)
        print ' done'

main()
