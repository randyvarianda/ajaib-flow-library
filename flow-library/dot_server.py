from portrait_export import portrait_get, portrait_post
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import sys,json,subprocess,tempfile,math
import numpy as np
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1];outdir=root;w,h=1440,810
dots=[]
for x in range(-12,1453,30):
 u=x/w;center=650-260*u+40*math.sin(u*5);width=105+45*u
 for y in range(150,811,30):
  v=(y-center)/width
  if abs(v)<=1:dots.append((x,y,u,v))
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(outdir),**kw)
 def do_GET(self):
  if not portrait_get(self):super().do_GET()
 def do_POST(self):
  if portrait_post(self):return
  if self.path!='/export-dots':self.send_error(404);return
  try:
   s=json.loads(self.rfile.read(int(self.headers['Content-Length'])));fmt=s['format'];assert fmt in ['mp4','webm'];mode=s['background'];assert mode in ['dark','blue','solid','gradient','transparent'];direction=s['direction'];assert direction in ['split','right','left'];speed=float(s['speed']);assert speed in [.5,1,2,4,8,16];intensity=max(.2,min(1,float(s['intensity'])));hex=s['color'];assert len(hex)==7 and hex[0]=='#';color=np.array([int(hex[i:i+2],16) for i in (1,3,5)])
   top,bottom=([24,76,208],[130,178,245]) if mode=='blue' else ([7,20,37],[16,43,70])
   if mode in ['solid','gradient']:
    def parse(value):
     assert len(value)==7 and value[0]=='#';return [int(value[i:i+2],16) for i in (1,3,5)]
    top=parse(s['color1']);bottom=parse(s['color2']) if mode=='gradient' else top
   ratio=(np.arange(h)+.5)/h;bg=np.array(top)[None,:]*(1-ratio[:,None])+np.array(bottom)[None,:]*ratio[:,None];cycles=max(1,round(speed/2));count=round(6/speed*cycles*60)
   with tempfile.TemporaryDirectory(dir=root/'work') as tmp:
    target=Path(tmp)/('dot-current.'+fmt);codec=['-c:v','libvpx-vp9','-pix_fmt','yuva420p','-auto-alt-ref','0','-b:v','0','-crf','24'] if fmt=='webm' else ['-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart']
    p=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{w}x{h}','-r','60','-i','-','-an',*codec,str(target)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for f in range(count):
     frame=np.zeros((h,w,4),np.uint8);transparent=mode=='transparent' and fmt=='webm'
     if not transparent:frame[:,:,:3]=np.uint8(bg[:,None,:]+.5);frame[:,:,3]=255
     for x,y,u,v in dots:
      sign=1 if direction=='right' else -1 if direction=='left' else 1 if v<0 else -1;cycle=(u-sign*f/count*cycles+v*.085)%1;dist=min(cycle,1-cycle);pulse=math.exp(-dist*dist/.013);alpha=(.12+pulse*.88*intensity)*min(1,(1-abs(v))*4);x0,x1=max(0,x-4),min(w,x+4);y0,y1=max(0,y-4),min(h,y+4)
      if x0>=x1 or y0>=y1:continue
      if transparent:frame[y0:y1,x0:x1,:3]=color;frame[y0:y1,x0:x1,3]=round(alpha*255)
      else:frame[y0:y1,x0:x1,:3]=np.uint8(color*alpha+bg[y0:y1,None,:]*(1-alpha)+.5)
     p.stdin.write(frame.tobytes())
    p.stdin.close();err=p.stderr.read();assert p.wait()==0,err;data=target.read_bytes();(outdir/('dot-current-custom.'+fmt)).write_bytes(data)
   self.send_response(200);self.send_header('Content-Type','video/'+fmt);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  except Exception as e:self.send_error(400,str(e))

