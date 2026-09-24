/**
 * NEW GYM — interactive realistic FBX athlete
 * Plays the original embedded Mixamo animation once per click.
 */
(function () {
  'use strict';

  const MODEL_URL = 'assets/models/realistic-athlete.fbx';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const state = { ready:false, playing:false, queued:false, reps:0, action:null };

  function injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      #gf-athlete-3d {
        position:fixed; right:6px; bottom:0; width:220px; height:380px;
        z-index:80; pointer-events:none; overflow:visible;
        filter:drop-shadow(0 18px 24px rgba(0,0,0,.62));
      }
      #gf-athlete-3d canvas { width:100%; height:100%; display:block; }
      #gf-athlete-loading {
        position:absolute; right:18px; bottom:24px; color:#c1ff6b;
        font:700 11px/1 Inter,sans-serif; letter-spacing:.08em;
        text-transform:uppercase; opacity:.72;
      }
      #gf-curl-counter {
        position:fixed; right:14px; bottom:350px; z-index:129;
        width:40px; height:40px; display:grid; place-items:center;
        border:2px solid #c1ff6b; border-radius:50%; color:#c1ff6b;
        background:rgba(8,12,0,.88); font:900 12px Inter,sans-serif;
        opacity:0; transform:scale(.8); transition:opacity .2s,transform .2s;
        pointer-events:none; box-shadow:0 5px 20px rgba(193,255,107,.22);
      }
      #gf-curl-counter.show { opacity:1; transform:scale(1); }
      .gf-rep-label {
        position:fixed; right:56px; bottom:342px; z-index:130;
        color:#c1ff6b; font:900 16px Inter,sans-serif;
        text-shadow:0 3px 15px rgba(193,255,107,.55);
        pointer-events:none; animation:gf-rep-float 1s ease-out forwards;
      }
      @keyframes gf-rep-float {
        0% { opacity:0; transform:translateY(8px) scale(.9); }
        25% { opacity:1; transform:translateY(0) scale(1); }
        100% { opacity:0; transform:translateY(-38px) scale(1); }
      }
      @media (max-width:900px) {
        #gf-athlete-3d { width:130px; height:225px; right:2px; bottom:58px; }
        #gf-curl-counter { right:7px; bottom:258px; width:32px; height:32px; }
        .gf-rep-label { right:44px; bottom:252px; font-size:12px; }
      }
      @media (max-width:480px) {
        #gf-athlete-3d { width:112px; height:198px; }
      }
    `;
    document.head.appendChild(style);
  }

  function createUI() {
    const wrap = document.createElement('div');
    wrap.id = 'gf-athlete-3d';
    wrap.setAttribute('aria-hidden', 'true');
    wrap.innerHTML = '<div id="gf-athlete-loading">Loading athlete…</div>';
    document.body.appendChild(wrap);

    const counter = document.createElement('div');
    counter.id = 'gf-curl-counter';
    counter.textContent = '0';
    document.body.appendChild(counter);
    return { wrap, counter };
  }

  function boot() {
    injectStyles();
    const { wrap, counter } = createUI();
    const THREE = window.THREE;
    if (!THREE?.FBXLoader) {
      wrap.remove();
      counter.remove();
      console.warn('[GF Athlete] Three.js FBXLoader is unavailable');
      return;
    }

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha:true, antialias:true, powerPreference:'high-performance' });
    } catch (error) {
      wrap.remove();
      counter.remove();
      console.warn('[GF Athlete] WebGL is unavailable', error);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.setClearColor(0x000000, 0);
    wrap.prepend(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(28, 1, .01, 100);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x182000, 2.2));
    const key = new THREE.DirectionalLight(0xffffff, 2.4);
    key.position.set(3,5,5);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0xc1ff6b, 1.1);
    rim.position.set(-4,3,-2);
    scene.add(rim);

    new THREE.FBXLoader().load(MODEL_URL, model => {
      model.traverse(object => {
        if (!object.isMesh) return;
        object.frustumCulled = false;
        if (object.material) {
          object.material = object.material.clone();
          object.material.roughness = .72;
          object.material.metalness = .03;
        }
      });

      const initialBox = new THREE.Box3().setFromObject(model);
      const initialSize = initialBox.getSize(new THREE.Vector3());
      model.scale.multiplyScalar(3.45 / Math.max(initialSize.y, .001));
      const box = new THREE.Box3().setFromObject(model);
      const center = box.getCenter(new THREE.Vector3());
      model.position.x -= center.x;
      model.position.y -= box.min.y;
      model.rotation.y = 0;
      scene.add(model);

      if (!model.animations?.length) throw new Error('The FBX has no embedded animation');
      const mixer = new THREE.AnimationMixer(model);
      const action = mixer.clipAction(model.animations[0]);
      action.setLoop(THREE.LoopOnce, 1);
      action.clampWhenFinished = true;
      action.play();
      action.paused = true;
      mixer.setTime(0);
      state.action = action;

      mixer.addEventListener('finished', () => {
        state.playing = false;
        state.reps++;
        counter.textContent = state.reps;
        counter.classList.add('show');
        showRepLabel();
        if (state.queued) { state.queued = false; playOriginalAnimation(); }
      });

      function resize() {
        const width = wrap.clientWidth || 300;
        const height = wrap.clientHeight || 500;
        renderer.setSize(width,height,false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
      }
      resize();
      window.addEventListener('resize',resize,{ passive:true });
      camera.position.set(0,1.8,7.7);
      camera.lookAt(0,1.65,0);

      state.ready = true;
      document.getElementById('gf-athlete-loading')?.remove();
      if (state.queued) {
        state.queued = false;
        playOriginalAnimation();
      }

      const clock = new THREE.Clock();
      function animate() {
        const delta = Math.min(clock.getDelta(),.05);
        if (state.playing && !reducedMotion) mixer.update(delta);
        renderer.render(scene,camera);
        requestAnimationFrame(animate);
      }
      requestAnimationFrame(animate);
    }, event => {
      const loading = document.getElementById('gf-athlete-loading');
      if (loading && event.total) loading.textContent = `Loading athlete ${Math.round(event.loaded/event.total*100)}%`;
    }, error => {
      wrap.remove();
      counter.remove();
      console.warn('[GF Athlete] Model failed to load',error);
    });
  }

  function playOriginalAnimation() {
    if (reducedMotion) return;
    if (!state.ready) { state.queued = true; return; }
    if (state.playing) { state.queued = true; return; }
    state.playing = true;
    state.action.reset();
    state.action.setLoop(window.THREE.LoopOnce,1);
    state.action.clampWhenFinished = true;
    state.action.paused = false;
    state.action.play();
  }
  window.gfTriggerCurl = playOriginalAnimation;

  function showRepLabel() {
    const label = document.createElement('div');
    label.className = 'gf-rep-label';
    label.textContent = '+1 Rep 🔥';
    document.body.appendChild(label);
    setTimeout(() => label.remove(),1050);
  }

  document.addEventListener('click',event => {
    if (['INPUT','SELECT','TEXTAREA'].includes(event.target.tagName)) return;
    playOriginalAnimation();
  });
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded',boot) : boot();
})();
