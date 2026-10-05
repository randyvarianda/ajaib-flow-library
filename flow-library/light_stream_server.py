from portrait_export import portrait_get, portrait_post
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import sys,json,subprocess,tempfile,numpy as np
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1];outdir=root;w,h=1280,720
x=(np.arange(w,dtype=np.float32)+.5)[None,:]/w;y=(np.arange(h,dtype=np.float32)+.5)[:,None]/h
paths=[.735+.035*i+.065*np.sin(x*4.4)-(.17-.055*i)*x*x for i in range(5)]
dists=[np.abs(y-p)*h for p in paths]
def col(s):
 assert len(s)==7 and s[0]=='#';return np.array([int(s[i:i+2],16)/255 for i in (1,3,5)])
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(outdir),**kw)
 def do_GET(self):
  if not portrait_get(self):super().do_GET()
 def do_POST(self):
  if portrait_post(self):return
  if self.path!='/export':self.send_error(404);return
  try:
   s=json.loads(self.rfile.read(int(self.headers['Content-Length'])));fmt=s['format'];assert fmt in ['mp4','webm'];a=col(s['color1']);b=col(s['color2']);mode=s['background'];assert mode in ['solid','gradient','transparent'];speed=max(.5,min(16,float(s['speed'])));strength=max(.2,min(2,float(s['strength'])));duration=6/speed;cycles=max(1,round(speed/2));count=round(duration*cycles*60)
   bg=np.broadcast_to(a,(h,w,3)) if mode!='gradient' else np.broadcast_to(a[None,None,:]*(1-y[:,:,None])+b[None,None,:]*y[:,:,None],(h,w,3))
   with tempfile.TemporaryDirectory(dir=root/'work') as td:
    target=Path(td)/('stream.'+fmt);codec=['-c:v','libvpx-vp9','-pix_fmt','yuva420p','-auto-alt-ref','0','-b:v','0','-crf','24'] if fmt=='webm' else ['-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart']
    p=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{w}x{h}','-r','60','-i','-','-an',*codec,str(target)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for f in range(count):
     phase=f/count*cycles*(-1 if s['reverse'] else 1);coverage=np.zeros((h,w),np.float32)
     for i,d in enumerate(dists):
      head=((phase+i*.23)%1)*1.5-.25;delta=head-x
      pulse=np.exp(-np.maximum(delta,0)**2/.011-np.minimum(delta,0)**2/.00015)
      light=np.exp(-d*d/1.2)*.52+strength*pulse*(np.exp(-d*d/4)*.8+np.exp(-d*d/90)*.24)
      coverage=1-(1-coverage)*(1-np.clip(light,0,1))
     if s['mirror']:coverage=coverage[:,::-1]
     rgb=np.broadcast_to(np.array([.83,.96,1.]),(h,w,3));alpha=coverage
     if mode!='transparent' or fmt=='mp4':rgb=rgb*alpha[:,:,None]+bg*(1-alpha[:,:,None]);alpha=np.ones_like(alpha)
     frame=np.dstack((rgb,alpha));p.stdin.write(np.uint8(np.clip(frame,0,1)*255+.5).tobytes())
    p.stdin.close();err=p.stderr.read();assert p.wait()==0,err;data=target.read_bytes();(outdir/('light-stream-custom.'+fmt)).write_bytes(data)
   self.send_response(200);self.send_header('Content-Type','video/'+fmt);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  except Exception as e:self.send_error(400,str(e))

