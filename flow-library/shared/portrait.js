(() => {
  const exportBase=new URL('../../',document.currentScript.src);
  const initialAspect=new URLSearchParams(location.search).get('aspect');
  let paint = () => {};
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = callback => raf(now => { callback(now); paint(); });
  window.addEventListener('DOMContentLoaded', () => {
    const source = document.querySelector('canvas');
    if (!source) return;
    const style = document.createElement('style');
    style.textContent = `.portrait-tools{padding:18px 4vw;display:flex;gap:14px;align-items:center;flex-wrap:wrap;border-bottom:1px solid #354660;font:14px system-ui;color:#edf5ff;background:#0b1424}.portrait-tools label{display:flex;align-items:center;gap:8px}.portrait-tools select,.portrait-tools button,.portrait-tools input[type=text]{font:inherit;border:1px solid #506a8e;background:#172b49;color:#edf5ff;padding:8px;border-radius:6px}.portrait-tools input[type=range]{width:90px}.portrait-tools input[type=text]{width:90px}.portrait-tools button{cursor:pointer}.portrait-tools [hidden]{display:none!important}.portrait-tools output{min-width:30px}.portrait-tools :focus-visible{outline:2px solid #80dfff;outline-offset:3px}.portrait-mode{display:block!important;aspect-ratio:auto!important;height:auto!important;max-width:none!important;background:#0b1424!important;position:relative;overflow:hidden}.portrait-mode>.portrait-source{position:absolute!important;left:-10000px!important;width:1920px!important;height:1080px!important;max-width:none!important}.portrait-mode>#portrait-canvas{display:block!important;width:min(100%,380px)!important;height:auto!important;aspect-ratio:9/16!important;margin:20px auto!important;background:none!important;transform:none!important}#portrait-canvas{display:none}`;
    document.head.append(style);
    const panel = document.createElement('div'); panel.className='portrait-tools';
    panel.innerHTML=`<label>Preview <select id="portrait-format"><option value="landscape">16:9 · Landscape</option><option value="portrait">9:16 · Portrait</option></select></label><label data-portrait>Framing <select id="portrait-fit"><option value="cover">Fill portrait</option><option value="contain">Whole flow</option></select></label><label data-portrait>Horizontal <input id="portrait-x" type="range" min="0" max="100" value="50"><output>50%</output></label><label data-portrait>Vertical <input id="portrait-y" type="range" min="0" max="100" value="50"><output>50%</output></label><label data-portrait>MP4 background <input id="portrait-matte" type="text" value="#071327" maxlength="7" aria-label="MP4 background hex"></label><label data-portrait>Duration <select id="portrait-duration"><option value="4">4 seconds</option><option value="6" selected>6 seconds</option><option value="8">8 seconds</option><option value="12">12 seconds</option></select></label><label data-portrait>Frame rate <select id="portrait-fps"><option value="30" selected>30 fps</option><option value="60">60 fps</option></select></label><button id="portrait-export" data-portrait>Export 9:16 MP4 · 1080 × 1920</button><span id="portrait-status" role="status"></span>`;
    const stage=source.parentElement; stage.before(panel);
    const target=document.createElement('canvas');target.id='portrait-canvas';target.width=1080;target.height=1920;target.setAttribute('aria-label','9:16 portrait flow preview');stage.append(target);source.classList.add('portrait-source');
    const ctx=target.getContext('2d',{alpha:false}),$=id=>document.getElementById(id),value=id=>$(id)?.value,valid=s=>/^#[0-9a-f]{6}$/i.test(s),safe=(v,f)=>valid(v)?v:f;
    let active=false,busy=false;
    function background() {
      const mode=value('backdrop')||value('background')||value('bg');
      let a=value('color1')||value('bg1')||value('bgHex'),b=value('color2')||value('bg2')||value('bgEnd');
      if(mode==='blue'){a='#184CD0';b='#82B2F5'}
      if(mode==='dark'){a='#071425';b='#102b46'}
      if(!a&&mode==='blue'){a='#1859df';b='#9fc6fc'}
      if(mode==='transparent'||mode==='clear'||!mode){a=value('portrait-matte');b=a}
      if(mode==='solid'){b=a}
      if(location.pathname.includes('light-aperture')){if(mode==='blue'){a='#1859df';b='#9fc6fc'}if(mode==='dark'){a=b='#071327'}}
      const g=ctx.createLinearGradient(0,0,0,1920);g.addColorStop(0,safe(a,'#071327'));g.addColorStop(1,safe(b,safe(a,'#071327')));return g;
    }
    paint=()=>{
      if(!active||!source.width||!source.height)return;
      ctx.fillStyle=background();ctx.fillRect(0,0,1080,1920);
      const fit=value('portrait-fit'),scale=fit==='cover'?Math.max(1080/source.width,1920/source.height):Math.min(1080/source.width,1920/source.height),w=source.width*scale,h=source.height*scale;
      const x=(1080-w)*Number(value('portrait-x'))/100,y=(1920-h)*Number(value('portrait-y'))/100;
      ctx.save();
      if(source.style.transform.includes('scaleX(-1)')){ctx.translate(1080,0);ctx.scale(-1,1)}
      ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';ctx.drawImage(source,x,y,w,h);ctx.restore();
    };
    const originalExports=['mp4','webm','export'].map(id=>$(id)).filter(Boolean);
    function setMode(){active=value('portrait-format')==='portrait';window.flowPortraitCompositing=active;stage.classList.toggle('portrait-mode',active);originalExports.forEach(el=>{el.style.display=active?'none':''});panel.querySelectorAll('[data-portrait]').forEach(el=>el.hidden=!active);$('portrait-status').textContent=active?'MP4 uses the background shown here. Keep this tab visible while recording.':'';}
    $('portrait-format').onchange=setMode;
    for(const id of ['portrait-x','portrait-y'])$(id).oninput=()=>$(id).nextElementSibling.textContent=value(id)+'%';
    if(initialAspect==='portrait')$('portrait-format').value='portrait';setMode();
    const numericStyle=document.createElement('style');numericStyle.textContent='input.slider-number{width:76px!important;padding:7px!important;border:1px solid #506a8e;border-radius:6px;background:#172b49;color:#edf5ff;font:inherit}';document.head.append(numericStyle);
    for(const slider of document.querySelectorAll('input[type=range]')){
      const field=document.createElement('input');field.type='number';field.className='slider-number';field.min=slider.min;field.max=slider.max;field.step=slider.step||'1';field.value=slider.value;
      field.setAttribute('aria-label',(slider.getAttribute('aria-label')||slider.id)+' value');
      const output=slider.nextElementSibling;
      if(output?.tagName==='OUTPUT'){output.hidden=true;output.after(field)}else slider.after(field);
      slider.addEventListener('input',()=>field.value=slider.value);
      field.addEventListener('input',()=>{if(field.value!==''&&field.validity.valid){slider.value=field.value;slider.dispatchEvent(new Event('input',{bubbles:true}))}});
      field.addEventListener('change',()=>{if(field.value!==''&&Number.isFinite(field.valueAsNumber)){slider.value=Math.max(Number(slider.min),Math.min(Number(slider.max),field.valueAsNumber));slider.dispatchEvent(new Event('input',{bubbles:true}))}field.value=slider.value});
    }
    $('portrait-export').onclick=async()=>{
      if(busy)return;
      const status=$('portrait-status');
      if(!valid(value('portrait-matte'))){status.textContent='Enter a background hex such as #071327.';return}
      const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/mp4'].find(m=>window.MediaRecorder?.isTypeSupported(m));
      if(!mime||!target.captureStream){status.textContent='Video recording is unavailable in this browser.';return}
      busy=true;let recorder,stream,timer,interrupted=false,resume=false,locked=[];
      const pause=$('play')||$('pause');
      const onHide=()=>{if(document.hidden&&recorder?.state==='recording'){interrupted=true;recorder.stop()}};
      try{
        const health=await fetch(new URL('portrait-health',exportBase));if(!health.ok)throw Error('Restart the Flow Library launcher to enable MP4 export.');
        if(pause&&pause.textContent.trim()==='Play'){pause.click();resume=true}
        locked=[...document.querySelectorAll('input,select,button')].map(el=>[el,el.disabled]);locked.forEach(([el])=>el.disabled=true);
        const fps=Number(value('portrait-fps')),duration=Number(value('portrait-duration'));
        stream=target.captureStream(fps);recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:24000000});const chunks=[];
        recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
        const finished=new Promise((resolve,reject)=>{recorder.onstop=resolve;recorder.onerror=()=>reject(Error('Recording failed.'))});
        document.addEventListener('visibilitychange',onHide);let left=duration;
        status.textContent=`Recording ${left}s — keep this tab visible`;recorder.start();
        timer=setInterval(()=>{left--;status.textContent=`Recording ${left}s — keep this tab visible`;if(left<=0){clearInterval(timer);if(recorder.state==='recording')recorder.stop()}},1000);
        await finished;clearInterval(timer);if(interrupted)throw Error('Recording stopped because this tab was hidden. Keep it visible and try again.');
        if(!chunks.length)throw Error('No frames recorded. Please try again.');
        status.textContent='Preparing portrait MP4…';
        const response=await fetch(new URL('export-portrait-mp4',exportBase),{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Frame-Rate':String(fps)},body:new Blob(chunks,{type:mime})});
        if(!response.ok)throw Error('MP4 conversion failed. Please retry.');
        const url=URL.createObjectURL(await response.blob()),link=document.createElement('a');link.href=url;link.download=document.title.replace(/[^a-z0-9]+/gi,'-').toLowerCase()+'-9x16.mp4';link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);status.textContent='Portrait MP4 exported · 1080 × 1920';
      }catch(error){status.textContent=error.message}
      finally{clearInterval(timer);document.removeEventListener('visibilitychange',onHide);if(recorder?.state==='recording')recorder.stop();stream?.getTracks().forEach(track=>track.stop());locked.forEach(([el,disabled])=>el.disabled=disabled);if(resume)pause.click();busy=false;}
    };
  });
})();
