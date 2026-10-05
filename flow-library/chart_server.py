from portrait_export import portrait_get, portrait_post
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import sys,json,math,tempfile,subprocess
import numpy as np
from PIL import Image,ImageDraw
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1];w,h=1440,810
values=[480+58*math.sin(i*math.pi*2/120*3)+27*math.sin(i*math.pi*2/120*11+.8)+17*math.sin(i*math.pi*2/120*23) for i in range(120)]
def rgb(v):
 assert len(v)==7 and v[0]=='#';return tuple(int(v[i:i+2],16) for i in (1,3,5))
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(root),**kw)
 def do_GET(self):
  if not portrait_get(self):super().do_GET()
 def do_POST(self):
  if portrait_post(self):return
  if self.path!='/export-chart':self.send_error(404);return
  try:
   s=json.loads(self.rfile.read(int(self.headers['Content-Length'])));fmt=s['format'];assert fmt in ['mp4','webm'];mode=s['mode'];assert mode in ['scroll','fixed'];speed=float(s['speed']);assert speed in [.5,1,2,4,8,16];color=rgb(s['color']);grid=rgb(s['gridColor']);a=rgb(s['bg1']);b=rgb(s['bg2']);bg=s['background'];assert bg in ['solid','gradient','transparent'];duration=(12 if mode=='scroll' else 6)/speed;cycles=max(1,math.ceil(3/duration));fps=int(s.get("fps",60));assert fps in [30,60];count=round(duration*cycles*fps)
   outw=int(s.get("resolution",1920));assert outw in [1920,2560];outh=outw*9//16;w=outw*3//2;h=w*9//16;scale=w/1440
   def points(coords):return tuple(v*scale for v in coords)
   def draw(image):
    raw=ImageDraw.Draw(image)
    class Scaled:
     def line(self,coords,fill,width):
      coords=[points(p) for p in coords] if isinstance(coords[0],tuple) else points(coords)
      raw.line(coords,fill=fill,width=max(1,round(width*scale)),joint="curve")
     def ellipse(self,coords,fill):raw.ellipse(points(coords),fill=fill)
    return Scaled()
   rows=np.arange(h)[:,None,None]/h;base=np.zeros((h,w,4),np.uint8)
   if bg!='transparent' or fmt=='mp4':base[:,:,:3]=np.array(a)*(1-rows)+np.array(b if bg=='gradient' else a)*rows;base[:,:,3]=255
   area=np.zeros((h,w,4),np.uint8);area[:,:,:3]=color;area[:,:,3]=np.uint8(np.clip((760-np.arange(h)/scale)/410,0,1)[:,None]*51)
   with tempfile.TemporaryDirectory(dir=root/'work') as tmp:
    target=Path(tmp)/('chart.'+fmt);codec=['-c:v','libvpx-vp9','-pix_fmt','yuva420p','-auto-alt-ref','0','-b:v','0','-crf','16','-deadline','good','-cpu-used','2'] if fmt=='webm' else ['-c:v','libx264','-pix_fmt','yuv420p','-crf','14','-preset','slow','-movflags','+faststart'];p=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{w}x{h}','-r',str(fps),'-i','-','-an','-vf',f'scale={outw}:{outh}:flags=lanczos',*codec,str(target)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for f in range(count):
     time=f/count*duration*cycles*speed;offset=time/12*120 if mode=='scroll' else 0
     def yy(x):
      u=(x/24+offset)%120;k=int(u);v=values[k]*(1-(u-k))+values[(k+1)%120]*(u-k);return v-(x*.12-80 if s['incline'] else 0)
     im=Image.fromarray(base);overlay=Image.new('RGBA',(w,h));d=draw(overlay)
     if s['grid']:
      for x in range(0,1441,80):d.line((x,310,x,750),fill=grid+(20,),width=1)
      for y in range(350,751,80):d.line((0,y,1440,y),fill=grid+(20,),width=1)
     im=Image.alpha_composite(im,overlay);pts=[(x,yy(x)) for x in range(-20,1441,4)]
     if s['fill']:
      mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon([points(p) for p in [(-20,760)]+pts+[(1440,760)]],fill=255);ar=Image.fromarray(area.copy());ar.putalpha(Image.fromarray(np.uint8(np.array(mask)/255*area[:,:,3])));im=Image.alpha_composite(im,ar)
     overlay=Image.new('RGBA',(w,h));d=draw(overlay);d.line(pts,fill=color+(217 if mode=='scroll' else 102,),width=2)
     if mode=='scroll':d.ellipse((1436,yy(1440)-4,1444,yy(1440)+4),fill=color+(255,))
     else:
      for j in range(2):
       head=((time/6+j*.5)%1)*1840-200
       for k in range(70):
        x=head-k*3
        if 0<=x<=1440:d.line((x,yy(x),x+3,yy(x+3)),fill=color+(round((1-k/70)*242),),width=3)
     im=Image.alpha_composite(im,overlay);p.stdin.write(im.tobytes())
    p.stdin.close();err=p.stderr.read();assert p.wait()==0,err;data=target.read_bytes();(root/('chart-flow-custom.'+fmt)).write_bytes(data)
   self.send_response(200);self.send_header('Content-Type','video/'+fmt);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  except Exception as e:self.send_error(400,str(e))

