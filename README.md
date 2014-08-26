# Right-to-left override CSS Generator

Copyright (c) 2014 Vision Advanced Systems

## Background

Unlike [my other script!](https://github.com/muayyad-alsadi/bootstrap-rtl/blob/c34e3ceac05bc7b134bde5a8ae4bfad7e7b59831/gen-rtl.sh)
which generates a replacement css file to be used instead of the original one. This script generate a CSS
that is to be included beside/after the original one because it only override RTL specific styles.

## How it works

given a CSS file like this

```
#main {background:white;text-align:left;}
.fancy-side {float:right;width:50%;}
.pretty-box {left:4px;width:50%;position:absolute;margin-right:20px;}
```

the output would be something like

```
#main {text-align:right;}
.fancy-side {float:left;}
.pretty-box {right:4px;left:auto;margin-left:20px;margin-right:0}
```

## Usage

```
RtlCss.py file1.css file2.min.css
```

given `file1.css` it will generate `file1.rtl.css`
given `file2.min.css` it will generate `file2.rtl.css` (notice that it ommit `min`)
