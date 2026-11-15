import json
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from PIL import Image, ImageDraw, ImageChops
S = r"D:/Code/VSCodeProjects/gojri-ai/data/ocr/pdfmarks-work"
_name2x = {k.split("|")[1]: v for k, v in json.load(open(S+"/fonts/map_all.json")).items()}
_tt = {}
def font(n):
    if n not in _tt: _tt[n] = TTFont(f"{S}/fonts/x{_name2x[n]}.ttf")
    return _tt[n]
def flat(rec, sc, ox, oy, H):
    contours=[]; cur=[]; pos=None
    def pt(p): return (ox+p[0]*sc, oy+H-p[1]*sc)
    for op,args in rec:
        if op=="moveTo": cur=[pt(args[0])]; pos=args[0]
        elif op=="lineTo": cur.append(pt(args[0])); pos=args[0]
        elif op=="qCurveTo":
            pts=list(args)
            # implied on-curve points
            offs=pts[:-1]; end=pts[-1]
            segs=[]
            for i,o in enumerate(offs):
                if i<len(offs)-1:
                    nxt=((o[0]+offs[i+1][0])/2,(o[1]+offs[i+1][1])/2)
                else: nxt=end
                segs.append((o,nxt))
            p0=pos
            for c,e in segs:
                for t in [i/6 for i in range(1,7)]:
                    x=(1-t)**2*p0[0]+2*(1-t)*t*c[0]+t*t*e[0]; y=(1-t)**2*p0[1]+2*(1-t)*t*c[1]+t*t*e[1]
                    cur.append(pt((x,y)))
                p0=e
            pos=end
        elif op=="curveTo":
            p0=pos; c1,c2,e=args
            for t in [i/6 for i in range(1,7)]:
                x=(1-t)**3*p0[0]+3*(1-t)**2*t*c1[0]+3*(1-t)*t*t*c2[0]+t**3*e[0]; y=(1-t)**3*p0[1]+3*(1-t)**2*t*c1[1]+3*(1-t)*t*t*c2[1]+t**3*e[1]
                cur.append(pt((x,y)))
            pos=e
        elif op in("closePath","endPath"):
            if cur: contours.append(cur); cur=[]
    return contours
def render(fn, gid, size=110):
    tt=font(fn); gname=tt.getGlyphOrder()[gid]; upm=tt["head"].unitsPerEm
    pen=DecomposingRecordingPen(tt.getGlyphSet()); tt.getGlyphSet()[gname].draw(pen)
    sc=size/upm*0.7
    im=Image.new("L",(size,size),255)
    base=int(size*0.7)
    acc=Image.new("L",(size,size),0)
    for c in flat(pen.value, sc, size*0.15, 0, base):
        m=Image.new("L",(size,size),0); ImageDraw.Draw(m).polygon(c,fill=255)
        acc=ImageChops.logical_xor(acc.convert("1"),m.convert("1")).convert("L")
    im=ImageChops.invert(acc)
    d=ImageDraw.Draw(im); d.line([(0,base),(size,base)],fill=200)
    return im
