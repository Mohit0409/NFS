(function () {
  'use strict';

  const x = (name,target,equipment,motion,tip,note='') => ({name,target,equipment,motion,tip,note});
  const E = {
    bench:x('Barbell Bench Press','Chest · Triceps','Barbell + bench','press','Keep your feet planted and shoulder blades gently set against the bench.'),
    inclinePress:x('Incline Dumbbell Press','Upper chest · Triceps','Dumbbells + incline bench','press','Press up and slightly inward without letting the shoulders roll forward.'),
    overheadPress:x('Overhead Press','Shoulders · Triceps','Barbell or dumbbells','overhead','Brace your trunk and finish with the weight stacked over your shoulders.'),
    pushup:x('Push-Up','Chest · Triceps · Core','Bodyweight','pushup','Keep head, ribs, hips and legs moving as one controlled line.'),
    lateralRaise:x('Dumbbell Lateral Raise','Side delts','Dumbbells','raise','Lead with the elbows and stop around shoulder height.'),
    tricepsPushdown:x('Cable Triceps Pushdown','Triceps','Cable','pushdown','Keep the upper arms quiet while the elbows straighten.'),
    latPulldown:x('Lat Pulldown','Lats · Upper back','Cable pulldown','pulldown','Pull the elbows toward your ribs instead of swinging your torso.'),
    barbellRow:x('Barbell Row','Mid back · Lats','Barbell','row','Hold a stable hip hinge and pull the bar toward the lower ribs.'),
    seatedRow:x('Seated Cable Row','Mid back · Lats','Cable','row','Stay tall and draw the elbows back without leaning far behind vertical.'),
    facePull:x('Face Pull','Rear delts · Upper back','Cable + rope','facepull','Pull toward eye level and let the hands separate as the elbows travel back.'),
    dbCurl:x('Dumbbell Curl','Biceps','Dumbbells','curl','Keep the elbow near your side and move through the elbow rather than the shoulder.'),
    hammerCurl:x('Hammer Curl','Biceps · Brachialis','Dumbbells','curl','Keep palms facing each other and avoid swinging the torso.'),
    backSquat:x('Back Squat','Quads · Glutes','Barbell + rack','squat','Keep pressure through the whole foot and let hips and knees bend together.'),
    frontSquat:x('Front Squat','Quads · Core','Barbell + rack','squat','Keep the elbows high and torso tall as you sit between the hips.'),
    legPress:x('Leg Press','Quads · Glutes','Leg press machine','squat','Lower only as far as you can keep your hips controlled against the pad.'),
    rdl:x('Romanian Deadlift','Hamstrings · Glutes','Barbell or dumbbells','hinge','Push the hips back with a long spine and keep the load close to the legs.'),
    deadlift:x('Conventional Deadlift','Glutes · Hamstrings · Back','Barbell','hinge','Brace before the pull and stand by driving the floor away, not yanking the bar.'),
    walkingLunge:x('Walking Lunge','Quads · Glutes','Bodyweight or dumbbells','lunge','Take a stable step and lower under control before driving through the front foot.'),
    legExtension:x('Leg Extension','Quads','Leg extension machine','kneeext','Control the final part of extension instead of kicking the weight up.'),
    standingCalf:x('Standing Calf Raise','Calves','Machine or bodyweight','calf','Pause briefly at the top and lower the heel through a comfortable range.'),
    dbFly:x('Dumbbell Fly','Chest','Dumbbells + bench','fly','Keep a soft bend in the elbows and open only as far as the shoulders stay comfortable.'),
    cableCross:x('Cable Crossover','Chest','Cable','fly','Bring the arms together with the chest rather than turning it into a press.'),
    machinePress:x('Chest Press Machine','Chest · Triceps','Chest press machine','press','Set the seat so the handles begin around mid-chest level.'),
    pullup:x('Pull-Up','Lats · Upper back','Pull-up bar','pullup','Start from a controlled hang and pull the chest toward the bar without kicking.'),
    oneArmRow:x('One-Arm Dumbbell Row','Lats · Mid back','Dumbbell + bench','row','Keep the torso stable and pull the elbow toward the back pocket.'),
    straightPulldown:x('Straight-Arm Pulldown','Lats','Cable','pulldown','Keep the elbows softly bent and sweep the arms toward the thighs.'),
    barbellCurl:x('Barbell Curl','Biceps','Barbell','curl','Keep wrists neutral and avoid throwing the hips forward.'),
    preacherCurl:x('Preacher Curl','Biceps','Preacher bench + curl bar','curl','Keep the upper arm supported and do not bounce out of the bottom.'),
    inclineCurl:x('Incline Dumbbell Curl','Biceps','Dumbbells + incline bench','curl','Let the arm hang naturally and curl without bringing the elbow forward.'),
    cableCurl:x('Cable Curl','Biceps','Cable','curl','Keep continuous tension and finish by bending the elbow, not shrugging.'),
    overheadTri:x('Overhead Triceps Extension','Triceps','Cable or dumbbell','tricepsOverhead','Keep elbows pointing mostly forward while straightening the arms overhead.'),
    closeBench:x('Close-Grip Bench Press','Triceps · Chest','Barbell + bench','press','Use a comfortable close grip and keep the forearms stacked under the bar.'),
    skull:x('Lying Triceps Extension','Triceps','EZ bar or dumbbells','skull','Keep the upper arms relatively still while the elbows bend and straighten.'),
    dip:x('Bench Dip','Triceps','Bench','dip','Keep the shoulders down and use a pain-free range; do not force depth.'),
    ropePush:x('Rope Pushdown','Triceps','Cable + rope','pushdown','Finish by separating the rope slightly without letting the shoulders roll forward.'),
    arnold:x('Arnold Press','Shoulders · Triceps','Dumbbells','overhead','Rotate smoothly while pressing; do not force the shoulder into an uncomfortable range.'),
    frontRaise:x('Front Raise','Front delts','Dumbbells or plate','frontraise','Raise under control to about shoulder height without leaning backward.'),
    reverseFly:x('Reverse Fly','Rear delts · Upper back','Dumbbells or machine','fly','Move from the shoulders with a soft elbow bend and avoid shrugging.'),
    wristCurl:x('Wrist Curl','Forearm flexors','Dumbbell or barbell','wrist','Support the forearm and move through the wrist without lifting the elbow.'),
    reverseWrist:x('Reverse Wrist Curl','Forearm extensors','Dumbbell or barbell','wrist','Use a light load and control both lifting and lowering.'),
    reverseCurl:x('Reverse Curl','Forearms · Brachialis','EZ bar or barbell','curl','Keep palms down and elbows close to the body.'),
    farmers:x("Farmer's Carry",'Grip · Forearms · Core','Dumbbells or kettlebells','carry','Walk tall with quiet shoulders and short controlled steps.'),
    platePinch:x('Plate Pinch Hold','Grip · Forearms','Weight plates','carry','Pinch the plates securely and keep the wrist straight rather than bent back.'),
    seatedCalf:x('Seated Calf Raise','Soleus · Calves','Seated calf machine','calf','Keep the knee position steady while moving through the ankle.'),
    singleCalf:x('Single-Leg Calf Raise','Calves','Bodyweight or dumbbell','calf','Use support for balance so the calf, not body sway, drives the rep.'),
    pressCalf:x('Leg Press Calf Press','Calves','Leg press machine','calf','Move only at the ankle and keep the knees softly extended, not locked hard.'),
    donkeyCalf:x('Donkey Calf Raise','Calves','Machine or bodyweight','calf','Keep the hips hinged and use a slow stretch-and-rise motion at the ankle.'),
    neckFlex:x('Neck Flexion','Front neck','Bodyweight / very light resistance','neckFlex','Use a small slow range and keep the movement comfortable.','Neck training should be light and controlled. Do not add load if you have neck pain, dizziness or a neck injury; ask a qualified professional first.'),
    neckExtend:x('Neck Extension','Back neck','Bodyweight / very light resistance','neckExtend','Move slowly and stop well before any pinching or discomfort.','Neck training should be light and controlled. Do not add load if you have neck pain, dizziness or a neck injury; ask a qualified professional first.'),
    neckSide:x('Lateral Neck Flexion','Side neck','Bodyweight / very light resistance','neckSide','Tilt gently ear toward shoulder without rotating the head.','Neck training should be light and controlled. Do not add load if you have neck pain, dizziness or a neck injury; ask a qualified professional first.'),
    neckRotate:x('Controlled Neck Rotation','Neck mobility','Bodyweight','neckRotate','Turn slowly within a comfortable range without forcing the end position.','Use this as gentle mobility, not a loaded strength drill. Stop if you feel dizziness, tingling or sharp pain.'),
    plank:x('Plank','Core','Bodyweight','plank','Brace as if preparing for a light punch and keep a straight line from head to heels.'),
    deadBug:x('Dead Bug','Core','Bodyweight','deadbug','Keep the lower back gently controlled as opposite arm and leg extend.'),
    birdDog:x('Bird Dog','Core · Glutes','Bodyweight','birddog','Reach long rather than high, keeping the hips square to the floor.'),
    cableCrunch:x('Cable Crunch','Abs','Cable','crunch','Curl the ribs toward the pelvis instead of pulling only with the arms.'),
    kneeRaise:x('Hanging Knee Raise','Abs · Hip flexors','Pull-up bar','kneeraise','Lift the knees with control and avoid swinging between reps.'),
    pallof:x('Pallof Press','Core · Anti-rotation','Cable or band','pallof','Press the hands away while resisting the cable trying to rotate your torso.'),
    hipThrust:x('Hip Thrust','Glutes','Bench + barbell','hipthrust','Finish by squeezing the glutes with ribs controlled rather than overextending the back.'),
    gluteBridge:x('Glute Bridge','Glutes','Bodyweight or load','hipthrust','Drive through the feet and stop when hips are extended without arching the lower back.'),
    bulgarian:x('Bulgarian Split Squat','Quads · Glutes','Bench + dumbbells','lunge','Keep a stable stance and lower the back knee under control.'),
    kickback:x('Cable Glute Kickback','Glutes','Cable','kickback','Move the thigh behind you without twisting the pelvis or arching the back.'),
    stepup:x('Step-Up','Quads · Glutes','Box or bench','stepup','Drive through the working leg and avoid pushing excessively from the trailing foot.'),
    sumo:x('Sumo Squat','Glutes · Quads · Adductors','Dumbbell or barbell','squat','Use a comfortable wider stance and let knees track with the toes.'),
    lyingCurl:x('Lying Leg Curl','Hamstrings','Leg curl machine','legcurl','Keep hips pressed into the pad as the knees bend.'),
    seatedCurl:x('Seated Leg Curl','Hamstrings','Seated leg curl machine','legcurl','Set the pad securely and control the return instead of letting the stack pull you back.'),
    goodMorning:x('Good Morning','Hamstrings · Glutes','Barbell','hinge','Use a light load, soft knees and a controlled hip hinge.'),
    nordic:x('Nordic Hamstring Curl','Hamstrings','Bodyweight + anchor','nordic','Lower only as far as you can control and use assistance when needed.'),
    singleRdl:x('Single-Leg Romanian Deadlift','Hamstrings · Glutes','Dumbbell or bodyweight','hinge','Keep the pelvis square and reach the free leg back as the torso hinges forward.'),
    goblet:x('Goblet Squat','Quads · Glutes · Core','Dumbbell or kettlebell','squat','Hold the load close to the chest and keep the whole foot connected to the floor.'),
    swing:x('Kettlebell Swing','Glutes · Hamstrings','Kettlebell','hinge','Drive the bell with a fast hip extension; the arms guide rather than lift it.')
  };

  const categories = [
    ['push','Push Day','Training day','Chest, shoulders and triceps pressing movements.',['bench','inclinePress','overheadPress','pushup','lateralRaise','tricepsPushdown']],
    ['pull','Pull Day','Training day','Back, rear-shoulder and biceps pulling movements.',['latPulldown','barbellRow','seatedRow','facePull','dbCurl','hammerCurl']],
    ['legs','Leg Day','Training day','A balanced lower-body mix for quads, glutes, hamstrings and calves.',['backSquat','legPress','rdl','walkingLunge','legExtension','standingCalf']],
    ['chest','Chest','Muscle group','Pressing and fly movements for the chest.',['bench','inclinePress','dbFly','cableCross','machinePress','pushup']],
    ['back','Back','Muscle group','Vertical and horizontal pulls for lats and upper back.',['latPulldown','pullup','barbellRow','oneArmRow','seatedRow','straightPulldown']],
    ['biceps','Biceps','Muscle group','Elbow-flexion variations with different grips and resistance.',['barbellCurl','dbCurl','hammerCurl','preacherCurl','inclineCurl','cableCurl']],
    ['triceps','Triceps','Muscle group','Pressing and elbow-extension movements for the triceps.',['tricepsPushdown','overheadTri','closeBench','skull','dip','ropePush']],
    ['shoulders','Shoulders','Muscle group','Presses and raises for front, side and rear delts.',['overheadPress','arnold','lateralRaise','frontRaise','reverseFly','facePull']],
    ['forearms','Forearms','Muscle group','Grip, wrist and reverse-curl work for forearm strength.',['wristCurl','reverseWrist','reverseCurl','farmers','platePinch']],
    ['calves','Calves','Muscle group','Standing, seated and single-leg ankle plantar-flexion work.',['standingCalf','seatedCalf','singleCalf','pressCalf','donkeyCalf']],
    ['neck','Neck','Muscle group','Gentle, controlled neck strength and mobility patterns.',['neckFlex','neckExtend','neckSide','neckRotate']],
    ['core','Core','Muscle group','Bracing, flexion and anti-rotation movements.',['plank','deadBug','birdDog','cableCrunch','kneeRaise','pallof']],
    ['glutes','Glutes','Muscle group','Hip extension and single-leg work for the glutes.',['hipThrust','gluteBridge','bulgarian','kickback','stepup','sumo']],
    ['hamstrings','Hamstrings','Muscle group','Hip-hinge and knee-flexion patterns for the hamstrings.',['rdl','lyingCurl','seatedCurl','goodMorning','nordic','singleRdl']],
    ['quads','Quads','Muscle group','Squat, press and knee-extension patterns for the front of the thigh.',['frontSquat','backSquat','legPress','legExtension','bulgarian','stepup']],
    ['fullbody','Full Body','Training style','Compound patterns that train several major areas together.',['deadlift','goblet','pushup','pullup','farmers','swing']]
  ].map(([id,name,kicker,copy,ids])=>({id,name,kicker,copy,ids}));

  const guides = {
    press:['Set shoulders securely on the bench and place feet firmly on the floor.','Lower with control, then press until the arms are comfortably extended.','Let the elbows flare excessively or bounce the load from the bottom.'],
    overhead:['Stand tall with ribs controlled and the load near shoulder level.','Press overhead on a smooth path, then lower under control.','Lean far backward or shrug hard into the neck.'],
    pushup:['Place hands securely and set a straight body line from head to heels.','Lower the chest under control, then press the floor away.','Let the hips sag or lead the rep with the head.'],
    raise:['Stand tall with a light controllable load and soft elbows.','Raise the arms smoothly to about shoulder height, then lower slowly.','Swing the torso or shrug the shoulders upward.'],
    frontraise:['Stand tall with the load in front of the thighs.','Raise the arms forward to about shoulder height and lower smoothly.','Lean backward to create momentum.'],
    pushdown:['Stand stable with elbows near the ribs.','Straighten the elbows, pause briefly, then return under control.','Let the elbows drift forward and back on every rep.'],
    tricepsOverhead:['Brace the torso and position the elbows around head level.','Bend and straighten at the elbows through a comfortable range.','Overarch the lower back or let elbows flare uncontrollably.'],
    pulldown:['Sit or stand tall and begin with the arms overhead.','Pull the elbows down toward the sides, then return with control.','Use a large backward body swing to move the weight.'],
    pullup:['Take a secure grip and begin from a controlled hang.','Pull the body upward, then lower without dropping into the bottom.','Kick or swing to create momentum.'],
    row:['Set a stable torso and let the arms reach without losing position.','Drive elbows back toward the body and squeeze the upper back.','Turn the movement into repeated torso rocking.'],
    facepull:['Set the cable around face height and stand firmly.','Pull toward the face while elbows travel out and back.','Finish with hands low or shrug shoulders toward ears.'],
    curl:['Stand or sit stable with elbows controlled.','Bend at the elbow, squeeze briefly, then lower slowly.','Swing the torso or let elbows travel far forward.'],
    squat:['Set a stable stance with the whole foot connected to the floor.','Bend hips and knees together, then stand by driving through the feet.','Let the heels lift or collapse the knees inward.'],
    lunge:['Take a stable split stance and keep the torso controlled.','Lower both knees, then drive through the front foot to rise.','Use a stance so narrow that balance is lost.'],
    stepup:['Place the working foot securely on the box or bench.','Drive through that leg to stand, then lower under control.','Jump off the trailing foot to make the rep easier.'],
    hinge:['Stand with soft knees and brace before moving.','Push hips back while the torso inclines, then squeeze glutes to stand.','Round the back or move the load away from the body.'],
    kneeext:['Set the machine so the knee joint aligns comfortably with its pivot.','Straighten the knees under control, pause, then lower slowly.','Kick the pad with momentum or slam the weight stack.'],
    legcurl:['Set the pad securely and keep hips stable.','Bend the knees to pull the pad, then return with control.','Lift the hips or rush the lowering phase.'],
    calf:['Stand or sit securely with the ball of the foot supported.','Rise through the ankle, pause, then lower the heel under control.','Bounce rapidly through the bottom position.'],
    fly:['Set the shoulders and keep a soft bend in the elbows.','Open and close the arms in a wide arc through a comfortable shoulder range.','Turn the fly into a deep stretch that pulls the shoulder forward.'],
    wrist:['Support the forearm and keep the elbow still.','Move the wrist slowly through a comfortable range, then return.','Use more load than the wrist can control.'],
    carry:['Pick up the load with a stable hinge and stand tall.','Walk with controlled steps while keeping trunk and shoulders quiet.','Lean sideways or let the weights swing into the legs.'],
    neckFlex:['Sit or stand tall with the upper body still.','Gently nod the head forward through a small comfortable range, then return.','Force the chin hard toward the chest or move quickly.'],
    neckExtend:['Sit or stand tall with the upper body still.','Gently move the head backward through a small comfortable range, then return.','Force the head far back or use heavy resistance.'],
    neckSide:['Sit or stand tall and look straight ahead.','Gently tilt one ear toward the same-side shoulder, then return.','Rotate the head while trying to side-bend it.'],
    neckRotate:['Sit or stand tall with eyes level.','Turn the head slowly left and right within a comfortable range.','Push into a painful end range or move quickly.'],
    plank:['Set forearms or hands under the shoulders and extend the legs.','Hold steady while breathing and maintaining trunk tension.','Let the hips sag or hold the breath.'],
    deadbug:['Lie on your back with hips and knees bent and arms up.','Slowly extend opposite arm and leg, then return and switch sides.','Let the lower back lift as the limbs reach away.'],
    birddog:['Start on hands and knees with a neutral trunk.','Reach opposite arm and leg long, pause, then switch sides.','Rotate the hips open or lift the leg too high.'],
    crunch:['Set the trunk tall or supported with the cable under control.','Bring ribs toward pelvis, then return slowly.','Pull only with the arms or crank on the neck.'],
    kneeraise:['Hang with shoulders controlled and legs quiet.','Lift knees toward the torso, then lower without swinging.','Build momentum by kicking the legs.'],
    pallof:['Stand side-on to the cable with hands held at the chest.','Press hands away while resisting rotation, then return.','Let the torso twist toward the cable.'],
    hipthrust:['Set upper back support securely and feet around hip width.','Drive hips upward, squeeze glutes, then lower with control.','Finish by arching the lower back instead of extending the hips.'],
    kickback:['Stand supported with the working leg free to move.','Extend the thigh behind you, then return without twisting the pelvis.','Swing the leg or overarch the lower back.'],
    dip:['Use a stable bench and keep shoulders down away from ears.','Bend and straighten the elbows through a comfortable range.','Force excessive shoulder depth.'],
    skull:['Lie securely with arms above the chest.','Keep upper arms controlled as elbows bend and straighten.','Turn the rep into a pullover by moving the whole upper arm.'],
    nordic:['Kneel with ankles securely anchored and hips extended.','Lower the body forward as one line using the hamstrings to resist.','Drop quickly into a range you cannot control.']
  };

  const modal=document.getElementById('exercise-modal');
  const grid=document.getElementById('exercise-grid');
  const tabs=document.getElementById('category-tabs');
  const search=document.getElementById('exercise-search');
  const canvas=document.getElementById('exercise-model');
  const ctx=canvas.getContext('2d');
  const $=id=>document.getElementById(id);
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let active='push', current=null, currentId='', started=performance.now(), raf=0, W=640, H=640;
  const catById=id=>categories.find(c=>c.id===id);
  const uniqueCount=new Set(categories.flatMap(c=>c.ids)).size;
  $('exercise-count').textContent=uniqueCount+' exercises';

  function renderTabs(){
    tabs.replaceChildren();
    categories.forEach(c=>{
      const b=document.createElement('button');
      b.className='category-tab'; b.type='button'; b.role='tab'; b.textContent=c.name; b.dataset.category=c.id;
      b.setAttribute('aria-selected',String(c.id===active));
      b.addEventListener('click',()=>{
        active=c.id; search.value=''; renderTabs(); renderGrid();
        window.gravityAnalytics?.event('exercise_category_view',{method:c.id});
      });
      tabs.appendChild(b);
    });
  }

  function renderGrid(){
    const c=catById(active), q=search.value.trim().toLowerCase();
    let ids=c.ids;
    if(q){
      ids=[...new Set(categories.flatMap(k=>k.ids))].filter(id=>{
        const e=E[id]; return [e.name,e.target,e.equipment].join(' ').toLowerCase().includes(q);
      });
      $('active-category-kicker').textContent='Search results';
      $('active-category-title').textContent='Search: '+search.value.trim();
      $('active-category-copy').textContent='Matches across every training day and muscle group.';
    } else {
      $('active-category-kicker').textContent=c.kicker; $('active-category-title').textContent=c.name; $('active-category-copy').textContent=c.copy;
    }
    grid.replaceChildren();
    ids.forEach((id,index)=>{
      const e=E[id], card=document.createElement('article');
      card.className='exercise-card';
      card.innerHTML='<div class="exercise-card__top"><span class="exercise-card__index">'+String(index+1).padStart(2,'0')+'</span><span class="exercise-card__motion">Movement guide</span></div><h3></h3><div class="exercise-card__meta"><span></span><span></span></div><button type="button">Watch movement</button>';
      card.querySelector('h3').textContent=e.name;
      const ms=card.querySelectorAll('.exercise-card__meta span');
      ms[0].textContent=e.target; ms[1].textContent=e.equipment;
      card.querySelector('button').addEventListener('click',()=>openExercise(id));
      grid.appendChild(card);
    });
    if(!ids.length){
      const p=document.createElement('p');
      p.className='exercise-empty';
      p.textContent='No exercise matched that search. Try a muscle group or a simpler exercise name.';
      grid.appendChild(p);
    }
    $('exercise-result-count').textContent=ids.length+' exercise'+(ids.length===1?'':'s');
  }
  search.addEventListener('input',renderGrid);

  function openExercise(id){
    current=E[id]; currentId=id; started=performance.now();
    const c=categories.find(k=>k.ids.includes(id));
    const g=guides[current.motion]||guides.carry;
    $('exercise-modal-category').textContent=(c?.name||'Exercise')+' · Animated guide';
    $('exercise-modal-title').textContent=current.name;
    $('exercise-modal-target').textContent='Target: '+current.target;
    $('exercise-modal-equipment').textContent='Equipment: '+current.equipment;
    $('exercise-modal-setup').textContent=g[0];
    $('exercise-modal-move').textContent=g[1];
    $('exercise-modal-tip').textContent=current.tip;
    $('exercise-modal-mistake').textContent=g[2];
    $('exercise-modal-note').textContent=current.note||'The animation is simplified for learning the movement pattern. Ask a New Gym coach for individual technique feedback.';
    if(typeof modal.showModal==='function') modal.showModal(); else modal.setAttribute('open','');
    window.gravityAnalytics?.event('exercise_demo_open',{method:id.slice(0,40)});
    drawLoop();
  }

  function closeModal(){
    if(modal.open) modal.close(); else modal.removeAttribute('open');
    cancelAnimationFrame(raf); current=null; currentId='';
  }
  $('exercise-modal-close').addEventListener('click',closeModal);
  modal.addEventListener('click',e=>{if(e.target===modal)closeModal();});
  modal.addEventListener('close',()=>{cancelAnimationFrame(raf);current=null;currentId='';});
  $('exercise-replay').addEventListener('click',()=>{
    started=performance.now();
    window.gravityAnalytics?.event('exercise_demo_replay',{method:currentId.slice(0,40)});
  });

  function P(x,y){return{x,y};}
  function base(){
    return {head:P(.5,.17),neck:P(.5,.25),sl:P(.43,.30),sr:P(.57,.30),el:P(.41,.43),er:P(.59,.43),hl:P(.40,.56),hr:P(.60,.56),pl:P(.47,.53),pr:P(.53,.53),kl:P(.46,.71),kr:P(.54,.71),al:P(.45,.89),ar:P(.55,.89)};
  }
  function shift(a,dy,dx=0){Object.keys(a).forEach(k=>{a[k]=P(a[k].x+dx,a[k].y+dy);});return a;}
  function pose(m,p){
    let a=base();
    const u=(1-Math.cos(p*Math.PI*2))/2;
    if(m==='press'){
      a.head=P(.73,.55);a.neck=P(.67,.56);a.sl=P(.61,.57);a.sr=P(.60,.59);a.pl=P(.40,.61);a.pr=P(.39,.63);
      a.kl=P(.29,.69);a.kr=P(.28,.71);a.al=P(.20,.84);a.ar=P(.20,.86);
      a.el=P(.56,.49-.12*u);a.er=P(.62,.49-.12*u);a.hl=P(.51,.40-.20*u);a.hr=P(.67,.40-.20*u);
    }
    else if(m==='curl'){
      a.hl=P(.44,.55-.19*u);a.hr=P(.56,.55-.19*u);a.el=P(.42,.43);a.er=P(.58,.43);
    }
    else if(m==='overhead'){
      a.el=P(.42,.40-.13*u);a.er=P(.58,.40-.13*u);a.hl=P(.40,.34-.19*u);a.hr=P(.60,.34-.19*u);
    }
    else if(m==='raise'){
      a.el=P(.39-.10*u,.43-.12*u);a.er=P(.61+.10*u,.43-.12*u);a.hl=P(.39-.22*u,.56-.26*u);a.hr=P(.61+.22*u,.56-.26*u);
    }
    else if(m==='frontraise'){
      a.el=P(.45,.43-.10*u);a.er=P(.55,.43-.10*u);a.hl=P(.46,.56-.24*u);a.hr=P(.54,.56-.24*u);
    }
    else if(m==='pushdown'){
      a.el=P(.43,.39);a.er=P(.57,.39);a.hl=P(.44,.45+.14*u);a.hr=P(.56,.45+.14*u);
    }
    else if(m==='tricepsOverhead'){
      a.el=P(.46,.25);a.er=P(.54,.25);a.hl=P(.48,.34-.17*u);a.hr=P(.52,.34-.17*u);
    }
    else if(m==='pulldown'){
      a.el=P(.39,.28+.12*u);a.er=P(.61,.28+.12*u);a.hl=P(.36,.12+.22*u);a.hr=P(.64,.12+.22*u);
    }
    else if(m==='pullup'){
      a.el=P(.43,.24+.10*u);a.er=P(.57,.24+.10*u);a.hl=P(.40,.10);a.hr=P(.60,.10);
      shift(a,-.08*u);a.hl=P(.40,.10);a.hr=P(.60,.10);
    }
    else if(m==='facepull'){
      a.el=P(.39,.41-.08*u);a.er=P(.61,.41-.08*u);a.hl=P(.50-.08*u,.42-.15*u);a.hr=P(.50+.08*u,.42-.15*u);
    }
    else if(m==='squat'){
      a.head.y+=.15*u;a.neck.y+=.15*u;a.sl.y+=.15*u;a.sr.y+=.15*u;a.el.y+=.15*u;a.er.y+=.15*u;a.hl.y+=.15*u;a.hr.y+=.15*u;
      a.pl=P(.45,.53+.17*u);a.pr=P(.55,.53+.17*u);a.kl=P(.39,.71+.05*u);a.kr=P(.61,.71+.05*u);
    }
    else if(m==='lunge'||m==='stepup'){
      shift(a,.10*u);a.pl=P(.47,.53+.09*u);a.pr=P(.53,.53+.09*u);a.kl=P(.38,.70+.02*u);a.al=P(.29,.84);a.kr=P(.58,.70+.08*u);a.ar=P(.64,.89);
    }
    else if(m==='hinge'||m==='row'){
      a.head=P(.68,.30+.06*u);a.neck=P(.62,.34+.06*u);a.sl=P(.58,.39+.06*u);a.sr=P(.61,.40+.06*u);a.pl=P(.47,.55);a.pr=P(.50,.55);
      a.kl=P(.44,.71);a.kr=P(.51,.71);a.al=P(.43,.89);a.ar=P(.52,.89);
      a.el=P(.58-.08*(m==='row'?u:0),.50);a.er=P(.61-.08*(m==='row'?u:0),.51);a.hl=P(.62-.16*(m==='row'?u:0),.62);a.hr=P(.65-.16*(m==='row'?u:0),.63);
    }
    else if(m==='kneeext'){
      a.head=P(.48,.20);a.neck=P(.48,.28);a.sl=P(.44,.33);a.sr=P(.52,.33);a.pl=P(.44,.54);a.pr=P(.50,.54);
      a.kl=P(.58,.62);a.kr=P(.62,.64);a.al=P(.62+.18*u,.83-.17*u);a.ar=P(.65+.16*u,.84-.16*u);
    }
    else if(m==='legcurl'){
      a.kl=P(.48,.70);a.kr=P(.55,.70);a.al=P(.45-.04*u,.88-.20*u);a.ar=P(.58+.04*u,.88-.20*u);
    }
    else if(m==='calf'){
      shift(a,-.035*u);a.al=P(.45,.89);a.ar=P(.55,.89);
    }
    else if(m==='fly'){
      a.el=P(.40-.12*(1-u),.34);a.er=P(.60+.12*(1-u),.34);a.hl=P(.29+.19*u,.34);a.hr=P(.71-.19*u,.34);
    }
    else if(m==='wrist'){
      a.el=P(.40,.45);a.er=P(.60,.45);a.hl=P(.39-.03*Math.sin(p*Math.PI*2),.57);a.hr=P(.61+.03*Math.sin(p*Math.PI*2),.57);
    }
    else if(m==='carry'){
      shift(a,0,.015*Math.sin(p*Math.PI*4));a.hl=P(.39,.58);a.hr=P(.61,.58);
    }
    else if(m==='neckFlex') a.head=P(.5,.17+.035*u);
    else if(m==='neckExtend') a.head=P(.5,.17-.03*u);
    else if(m==='neckSide') a.head=P(.5+.035*Math.sin(p*Math.PI*2),.17);
    else if(m==='neckRotate') a.head=P(.5+.025*Math.sin(p*Math.PI*2),.17);
    else if(m==='plank'||m==='pushup'){
      const bob=.05*u*(m==='pushup');
      a.head=P(.73,.44+bob);a.neck=P(.67,.46+bob);a.sl=P(.62,.48+bob);a.sr=P(.61,.50+bob);a.pl=P(.40,.52+bob);a.pr=P(.39,.54+bob);
      a.kl=P(.27,.56+bob);a.kr=P(.27,.58+bob);a.al=P(.14,.60+bob);a.ar=P(.14,.62+bob);a.el=P(.63,.61-.07*u*(m==='pushup'));a.er=P(.60,.61-.07*u*(m==='pushup'));a.hl=P(.58,.72);a.hr=P(.64,.72);
    }
    else if(m==='deadbug'){
      a.head=P(.72,.55);a.neck=P(.66,.56);a.sl=P(.61,.57);a.sr=P(.60,.59);a.pl=P(.42,.60);a.pr=P(.41,.62);
      a.el=P(.59-.10*u,.43);a.er=P(.57,.45);a.hl=P(.53-.15*u,.29);a.hr=P(.52,.31);a.kl=P(.33,.48);a.kr=P(.34,.65);a.al=P(.25-.10*u,.34);a.ar=P(.20,.70);
    }
    else if(m==='birddog'){
      a.head=P(.70,.43);a.neck=P(.64,.46);a.sl=P(.58,.48);a.sr=P(.56,.50);a.pl=P(.42,.54);a.pr=P(.40,.56);
      a.kl=P(.35,.68);a.kr=P(.43,.68);a.al=P(.32-.16*u,.78-.10*u);a.ar=P(.43,.80);a.el=P(.60,.61);a.er=P(.55,.62);a.hl=P(.57+.17*u,.72-.13*u);a.hr=P(.54,.74);
    }
    else if(m==='crunch'){
      a.head=P(.68-.10*u,.53-.11*u);a.neck=P(.63-.09*u,.56-.09*u);a.sl=P(.58-.07*u,.58-.07*u);a.sr=P(.57-.07*u,.60-.07*u);
      a.pl=P(.40,.62);a.pr=P(.39,.64);a.kl=P(.29,.53);a.kr=P(.28,.55);a.al=P(.20,.68);a.ar=P(.20,.70);
    }
    else if(m==='kneeraise'){
      a.hl=P(.42,.10);a.hr=P(.58,.10);a.el=P(.44,.24);a.er=P(.56,.24);a.kl=P(.44,.70-.18*u);a.kr=P(.56,.70-.18*u);a.al=P(.44,.88-.25*u);a.ar=P(.56,.88-.25*u);
    }
    else if(m==='pallof'){
      a.el=P(.44,.40);a.er=P(.56,.40);a.hl=P(.48-.04*u,.48-.12*u);a.hr=P(.52+.04*u,.48-.12*u);
    }
    else if(m==='hipthrust'){
      a.head=P(.72,.58);a.neck=P(.66,.58);a.sl=P(.61,.58);a.sr=P(.59,.60);a.pl=P(.42,.65-.15*u);a.pr=P(.40,.66-.15*u);
      a.kl=P(.29,.68);a.kr=P(.28,.70);a.al=P(.20,.83);a.ar=P(.20,.85);
    }
    else if(m==='kickback'){
      a.kl=P(.46,.70);a.kr=P(.54,.70);a.al=P(.44-.12*u,.88-.08*u);a.ar=P(.56,.88);
    }
    else if(m==='dip'){
      a.head=P(.52,.24+.08*u);a.neck=P(.52,.31+.08*u);a.sl=P(.48,.35+.08*u);a.sr=P(.56,.35+.08*u);a.el=P(.43,.47+.02*u);a.er=P(.61,.47+.02*u);a.hl=P(.42,.54);a.hr=P(.62,.54);a.pl=P(.49,.56+.08*u);a.pr=P(.55,.56+.08*u);
    }
    else if(m==='skull'){
      a.head=P(.72,.55);a.neck=P(.66,.56);a.sl=P(.60,.57);a.sr=P(.59,.59);a.pl=P(.40,.61);a.pr=P(.39,.63);a.el=P(.58,.38);a.er=P(.56,.40);a.hl=P(.64-.08*u,.28+.16*u);a.hr=P(.60-.08*u,.30+.16*u);
    }
    else if(m==='nordic'){
      a.kl=P(.44,.78);a.kr=P(.52,.78);a.al=P(.42,.89);a.ar=P(.54,.89);a.pl=P(.46+.10*u,.58+.05*u);a.pr=P(.52+.10*u,.58+.05*u);a.sl=P(.43+.20*u,.33+.12*u);a.sr=P(.57+.20*u,.33+.12*u);a.head=P(.5+.22*u,.20+.14*u);a.neck=P(.5+.20*u,.27+.13*u);
    }
    return a;
  }

  function line(a,b,w=12,color='#d9b56f'){
    ctx.strokeStyle=color;ctx.lineWidth=w;ctx.lineCap='round';ctx.beginPath();ctx.moveTo(a.x*W,a.y*H);ctx.lineTo(b.x*W,b.y*H);ctx.stroke();
  }
  function joint(a,r=8){ctx.fillStyle='#f3e5c8';ctx.beginPath();ctx.arc(a.x*W,a.y*H,r,0,Math.PI*2);ctx.fill();}

  function drawModel(time){
    const rect=canvas.getBoundingClientRect(), dpr=Math.min(window.devicePixelRatio||1,2);
    W=Math.max(320,rect.width); H=Math.max(320,rect.height);
    const pw=Math.round(W*dpr), ph=Math.round(H*dpr);
    if(canvas.width!==pw||canvas.height!==ph){canvas.width=pw;canvas.height=ph;}
    ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,W,H);
    const phase=reduced?.2:((time-started)%2400)/2400;
    const a=pose(current?.motion||'carry',phase);
    ctx.strokeStyle='rgba(211,168,92,.18)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(W*.10,H*.90);ctx.lineTo(W*.90,H*.90);ctx.stroke();
    if(['press','skull'].includes(current?.motion)){
      ctx.fillStyle='rgba(211,168,92,.12)';ctx.fillRect(W*.20,H*.66,W*.58,H*.035);ctx.fillRect(W*.30,H*.69,W*.03,H*.17);ctx.fillRect(W*.69,H*.69,W*.03,H*.17);
    }
    line(a.neck,a.sl,8);line(a.neck,a.sr,8);line(a.sl,a.pl,15,'#c69a50');line(a.sr,a.pr,15,'#c69a50');line(a.pl,a.pr,12);
    line(a.sl,a.el,13);line(a.el,a.hl,11);line(a.sr,a.er,13);line(a.er,a.hr,11);line(a.pl,a.kl,15);line(a.kl,a.al,13);line(a.pr,a.kr,15);line(a.kr,a.ar,13);
    [a.sl,a.sr,a.el,a.er,a.hl,a.hr,a.pl,a.pr,a.kl,a.kr,a.al,a.ar].forEach(v=>joint(v,5));
    ctx.fillStyle='#f0d8a7';ctx.beginPath();ctx.arc(a.head.x*W,a.head.y*H,Math.min(W,H)*.043,0,Math.PI*2);ctx.fill();line(a.head,a.neck,7,'#e7c886');
    const eq=(current?.equipment||'').toLowerCase();
    if(eq.includes('dumbbell')){
      [a.hl,a.hr].forEach(h=>{ctx.strokeStyle='#d9d4ca';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(h.x*W-12,h.y*H);ctx.lineTo(h.x*W+12,h.y*H);ctx.stroke();});
    }
    if(eq.includes('barbell')||eq.includes('curl bar')||eq.includes('ez bar')){
      ctx.strokeStyle='#d6d2ca';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(a.hl.x*W-26,a.hl.y*H);ctx.lineTo(a.hr.x*W+26,a.hr.y*H);ctx.stroke();
    }
    if(eq.includes('cable')){
      ctx.strokeStyle='rgba(214,210,202,.55)';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(W*.92,H*.12);ctx.lineTo(a.hr.x*W,a.hr.y*H);ctx.stroke();
    }
    if(current?.motion==='pullup'){
      ctx.strokeStyle='#d6d2ca';ctx.lineWidth=7;ctx.beginPath();ctx.moveTo(W*.30,H*.10);ctx.lineTo(W*.70,H*.10);ctx.stroke();
    }
    ctx.fillStyle='rgba(240,216,167,.7)';ctx.font='700 12px Inter, sans-serif';ctx.textAlign='center';ctx.fillText('MOVEMENT LOOP',W*.5,H*.965);
  }

  function drawLoop(){
    cancelAnimationFrame(raf);
    const tick=t=>{
      if(!current||!modal.open)return;
      drawModel(t);
      raf=requestAnimationFrame(tick);
    };
    raf=requestAnimationFrame(tick);
  }

  window.addEventListener('resize',()=>{if(current)drawModel(performance.now());},{passive:true});
  renderTabs();
  renderGrid();
  const requestedExercise=new URLSearchParams(window.location.search).get('exercise');
  if(requestedExercise && E[requestedExercise]) openExercise(requestedExercise);
})();
