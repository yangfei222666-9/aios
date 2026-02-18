// Super Mario - Game Engine
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');

// === Config ===
const TILE = 32;
const GRAVITY = 0.5;
const FRICTION = 0.8;
const MAX_SPEED = 4;
const JUMP_FORCE = -10;
const ENEMY_SPEED = 1;

let W, H, scale = 1;
function resize() {
  const aspect = 16 / 12;
  W = Math.min(window.innerWidth, 800);
  H = W / aspect;
  canvas.width = W; canvas.height = H;
  scale = W / (25 * TILE);
}
resize();
window.addEventListener('resize', resize);

// === State ===
let gameState = 'start'; // start | play | over
let score = 0, coins = 0, timer = 400;
let cameraX = 0;

// === Colors ===
const COLORS = {
  sky: '#6b8cff', ground: '#c84c0c', brick: '#c84c0c', brickLine: '#e09050',
  question: '#e09050', questionMark: '#fff', coin: '#ffd700',
  pipe: '#00a800', pipeDark: '#006800',
  mario: '#e52521', marioSkin: '#ffb89a', marioHat: '#e52521',
  marioOveralls: '#6b6bff', marioBoot: '#6b3c00',
  goomba: '#c84c0c', goombaDark: '#6b3c00',
  cloud: '#fff', bush: '#00a800', hill: '#5a9400',
};

// === Level Map ===
// 0=air, 1=ground, 2=brick, 3=question, 4=pipe-left, 5=pipe-right, 6=pipe-top-l, 7=pipe-top-r
const LEVEL_W = 120;
const LEVEL_H = 14;
const level = [];
for (let y = 0; y < LEVEL_H; y++) {
  level[y] = new Array(LEVEL_W).fill(0);
}
// Ground
for (let x = 0; x < LEVEL_W; x++) {
  if ((x >= 69 && x <= 70) || (x >= 86 && x <= 88)) continue; // gaps
  level[12][x] = 1; level[13][x] = 1;
}
// Question blocks
[[16,8],[21,8],[22,4],[23,8]].forEach(([x,y]) => level[y][x] = 3);
// Bricks
[[20,8],[24,8],[77,8],[78,8],[79,4],[80,4],[81,4],[82,4],[83,4],[84,4],[85,4],[86,4]].forEach(([x,y]) => level[y][x] = 2);
// Pipes
function addPipe(x, h) {
  level[12-h][x] = 6; level[12-h][x+1] = 7;
  for (let i = 1; i < h; i++) { level[12-h+i][x] = 4; level[12-h+i][x+1] = 5; }
}
addPipe(28, 2); addPipe(38, 3); addPipe(46, 4); addPipe(57, 4);
// Stairs near end
for (let i = 0; i < 4; i++) for (let j = 0; j <= i; j++) level[11-j][93+i] = 1;
for (let i = 0; i < 4; i++) for (let j = 0; j <= i; j++) level[11-j][100-i] = 1;
for (let i = 0; i < 8; i++) for (let j = 0; j <= i; j++) level[11-j][105+i] = 1;

// === Entities ===
const mario = { x: 3*TILE, y: 10*TILE, vx: 0, vy: 0, w: 24, h: 30, dir: 1, grounded: false, dead: false };

let enemies = [
  { x: 22*TILE, y: 11*TILE, vx: -ENEMY_SPEED, w: 28, h: 28, alive: true, type: 'goomba' },
  { x: 40*TILE, y: 11*TILE, vx: -ENEMY_SPEED, w: 28, h: 28, alive: true, type: 'goomba' },
  { x: 51*TILE, y: 11*TILE, vx: -ENEMY_SPEED, w: 28, h: 28, alive: true, type: 'goomba' },
  { x: 52*TILE, y: 11*TILE, vx: -ENEMY_SPEED, w: 28, h: 28, alive: true, type: 'goomba' },
  { x: 80*TILE, y: 11*TILE, vx: -ENEMY_SPEED, w: 28, h: 28, alive: true, type: 'goomba' },
];

let particles = []; // coin pop, brick break
let questionHit = new Set();

// === Input ===
const keys = {};
window.addEventListener('keydown', e => {
  keys[e.code] = true;
  if (gameState === 'start') { gameState = 'play'; document.getElementById('start-screen').classList.add('hidden'); }
  if (gameState === 'over') restartGame();
});
window.addEventListener('keyup', e => keys[e.code] = false);

// Touch
['btn-left','btn-right','btn-jump'].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  const code = id === 'btn-left' ? 'ArrowLeft' : id === 'btn-right' ? 'ArrowRight' : 'Space';
  el.addEventListener('touchstart', e => { e.preventDefault(); keys[code] = true;
    if (gameState === 'start') { gameState = 'play'; document.getElementById('start-screen').classList.add('hidden'); }
    if (gameState === 'over') restartGame();
  });
  el.addEventListener('touchend', e => { e.preventDefault(); keys[code] = false; });
});
document.addEventListener('touchstart', e => {
  if (gameState === 'start') { gameState = 'play'; document.getElementById('start-screen').classList.add('hidden'); }
});

// === Collision ===
function getTile(px, py) {
  const tx = Math.floor(px / TILE), ty = Math.floor(py / TILE);
  if (tx < 0 || tx >= LEVEL_W || ty < 0 || ty >= LEVEL_H) return 0;
  return level[ty][tx];
}
function isSolid(t) { return t >= 1; }

function collideX(ent) {
  const left = Math.floor(ent.x / TILE), right = Math.floor((ent.x + ent.w - 1) / TILE);
  const top = Math.floor(ent.y / TILE), bot = Math.floor((ent.y + ent.h - 1) / TILE);
  for (let ty = top; ty <= bot; ty++) {
    for (let tx = left; tx <= right; tx++) {
      if (isSolid(getTile(tx * TILE, ty * TILE))) {
        if (ent.vx > 0) { ent.x = tx * TILE - ent.w; ent.vx = 0; }
        else if (ent.vx < 0) { ent.x = (tx + 1) * TILE; ent.vx = 0; }
        return true;
      }
    }
  }
  return false;
}

function collideY(ent) {
  const left = Math.floor(ent.x / TILE), right = Math.floor((ent.x + ent.w - 1) / TILE);
  const top = Math.floor(ent.y / TILE), bot = Math.floor((ent.y + ent.h - 1) / TILE);
  for (let ty = top; ty <= bot; ty++) {
    for (let tx = left; tx <= right; tx++) {
      if (isSolid(getTile(tx * TILE, ty * TILE))) {
        if (ent.vy > 0) { ent.y = ty * TILE - ent.h; ent.vy = 0; ent.grounded = true; }
        else if (ent.vy < 0) {
          ent.y = (ty + 1) * TILE; ent.vy = 0;
          hitBlock(tx, ty);
        }
        return true;
      }
    }
  }
  return false;
}

function hitBlock(tx, ty) {
  const t = level[ty][tx];
  const key = tx + ',' + ty;
  if (t === 3 && !questionHit.has(key)) {
    questionHit.add(key);
    coins++; score += 200;
    particles.push({ x: tx*TILE+8, y: ty*TILE-16, vy: -6, life: 30, type: 'coin' });
  }
  if (t === 2) {
    level[ty][tx] = 0;
    score += 50;
    for (let i = 0; i < 4; i++) {
      particles.push({ x: tx*TILE+8+Math.random()*16, y: ty*TILE, vx: (Math.random()-0.5)*4, vy: -4-Math.random()*3, life: 25, type: 'debris' });
    }
  }
}

function boxOverlap(a, b) {
  return a.x < b.x+b.w && a.x+a.w > b.x && a.y < b.y+b.h && a.y+a.h > b.y;
}

// === Update ===
let timerAcc = 0;
function update() {
  if (gameState !== 'play') return;
  const m = mario;

  // Input
  if (keys['ArrowLeft'] || keys['KeyA']) { m.vx -= 0.5; m.dir = -1; }
  if (keys['ArrowRight'] || keys['KeyD']) { m.vx += 0.5; m.dir = 1; }
  if ((keys['Space'] || keys['ArrowUp'] || keys['KeyW']) && m.grounded) { m.vy = JUMP_FORCE; m.grounded = false; }

  // Physics
  if (!keys['ArrowLeft'] && !keys['KeyA'] && !keys['ArrowRight'] && !keys['KeyD']) m.vx *= FRICTION;
  m.vx = Math.max(-MAX_SPEED, Math.min(MAX_SPEED, m.vx));
  m.vy += GRAVITY;
  if (m.vy > 12) m.vy = 12;

  m.grounded = false;
  m.x += m.vx; collideX(m);
  m.y += m.vy; collideY(m);

  if (m.x < 0) m.x = 0;

  // Camera
  const targetCam = m.x - W/(2*scale) + m.w/2;
  cameraX = Math.max(0, Math.min(targetCam, (LEVEL_W*TILE - W/scale)));

  // Fall death
  if (m.y > LEVEL_H * TILE) { gameState = 'over'; document.getElementById('game-over').classList.remove('hidden'); return; }

  // Enemies
  enemies.forEach(e => {
    if (!e.alive) return;
    if (Math.abs(e.x - m.x) > W) return; // skip far enemies
    e.x += e.vx;
    e.vy = (e.vy || 0) + GRAVITY;
    e.y += e.vy;
    // ground
    const bot = Math.floor((e.y + e.h) / TILE);
    const tx = Math.floor((e.x + e.w/2) / TILE);
    if (bot < LEVEL_H && isSolid(level[bot]?.[tx])) { e.y = bot * TILE - e.h; e.vy = 0; }
    // wall
    const ahead = Math.floor((e.x + (e.vx > 0 ? e.w : 0)) / TILE);
    const mid = Math.floor((e.y + e.h/2) / TILE);
    if (isSolid(level[mid]?.[ahead])) e.vx *= -1;
    // fall
    if (e.y > LEVEL_H * TILE) e.alive = false;

    // Mario collision
    if (boxOverlap(m, e)) {
      if (m.vy > 0 && m.y + m.h - e.y < 16) {
        e.alive = false; score += 100; m.vy = JUMP_FORCE * 0.6;
        particles.push({ x: e.x, y: e.y, life: 15, type: 'squash' });
      } else {
        gameState = 'over'; document.getElementById('game-over').classList.remove('hidden');
      }
    }
  });

  // Particles
  particles.forEach(p => {
    p.life--;
    if (p.vy !== undefined) p.vy += 0.3;
    if (p.vy !== undefined) p.y += p.vy;
    if (p.vx !== undefined) p.x += p.vx;
  });
  particles = particles.filter(p => p.life > 0);

  // Timer
  timerAcc++;
  if (timerAcc >= 24) { timerAcc = 0; timer--; if (timer <= 0) { gameState = 'over'; document.getElementById('game-over').classList.remove('hidden'); } }

  // Win
  if (m.x > 113 * TILE) { score += timer * 50; timer = 0; gameState = 'over'; document.getElementById('game-over').querySelector('h1').textContent = 'YOU WIN!'; document.getElementById('game-over').classList.remove('hidden'); }

  // UI
  document.getElementById('score').textContent = String(score).padStart(6, '0');
  document.getElementById('coins').textContent = '×' + String(coins).padStart(2, '0');
  document.getElementById('time').textContent = timer;
}

// === Draw ===
function drawTile(tx, ty, t) {
  const x = tx * TILE - cameraX, y = ty * TILE;
  if (x < -TILE || x > W/scale + TILE) return;
  if (t === 1) { // ground
    ctx.fillStyle = COLORS.ground; ctx.fillRect(x, y, TILE, TILE);
    ctx.fillStyle = '#e09050'; ctx.fillRect(x+2, y+2, TILE-4, TILE-4);
    ctx.fillStyle = COLORS.ground;
    ctx.fillRect(x+4, y+12, TILE-8, 2);
    ctx.fillRect(x+12, y+4, 2, TILE-8);
  } else if (t === 2) { // brick
    ctx.fillStyle = COLORS.brick; ctx.fillRect(x, y, TILE, TILE);
    ctx.fillStyle = COLORS.brickLine;
    ctx.fillRect(x+1, y+1, 14, 14); ctx.fillRect(x+17, y+1, 14, 14);
    ctx.fillRect(x+9, y+17, 14, 14);
  } else if (t === 3) { // question
    const key = tx+','+ty;
    ctx.fillStyle = questionHit.has(key) ? '#8b6914' : COLORS.question;
    ctx.fillRect(x, y, TILE, TILE);
    ctx.strokeStyle = '#000'; ctx.lineWidth = 1; ctx.strokeRect(x, y, TILE, TILE);
    if (!questionHit.has(key)) {
      ctx.fillStyle = COLORS.questionMark; ctx.font = 'bold 18px sans-serif'; ctx.textAlign = 'center';
      ctx.fillText('?', x+TILE/2, y+TILE/2+6);
    }
  } else if (t === 4 || t === 5) { // pipe body
    ctx.fillStyle = t === 4 ? COLORS.pipe : COLORS.pipeDark; ctx.fillRect(x, y, TILE, TILE);
    if (t === 4) { ctx.fillStyle = COLORS.pipeDark; ctx.fillRect(x, y, 4, TILE); }
    else { ctx.fillStyle = '#50e850'; ctx.fillRect(x+TILE-4, y, 4, TILE); }
  } else if (t === 6 || t === 7) { // pipe top
    ctx.fillStyle = COLORS.pipe; ctx.fillRect(x - (t===6?4:0), y, TILE + (t===6?4:0), TILE);
    ctx.fillStyle = COLORS.pipeDark;
    if (t === 6) ctx.fillRect(x-4, y, 6, TILE);
    else ctx.fillRect(x+TILE-2, y, 6, TILE);
    ctx.fillStyle = '#50e850';
    if (t === 7) ctx.fillRect(x+TILE+2, y, 2, TILE);
  }
}

function drawMario() {
  const m = mario;
  const x = m.x - cameraX, y = m.y;
  const d = m.dir;
  // Hat
  ctx.fillStyle = COLORS.marioHat;
  ctx.fillRect(x + (d>0?4:2), y, 18, 8);
  // Face
  ctx.fillStyle = COLORS.marioSkin;
  ctx.fillRect(x+4, y+8, 16, 8);
  // Eyes
  ctx.fillStyle = '#000';
  ctx.fillRect(x + (d>0?14:6), y+10, 3, 3);
  // Body
  ctx.fillStyle = COLORS.mario;
  ctx.fillRect(x+2, y+16, 20, 6);
  // Overalls
  ctx.fillStyle = COLORS.marioOveralls;
  ctx.fillRect(x+4, y+22, 16, 4);
  // Boots
  ctx.fillStyle = COLORS.marioBoot;
  ctx.fillRect(x+2, y+26, 8, 4);
  ctx.fillRect(x+14, y+26, 8, 4);
}

function drawGoomba(e) {
  const x = e.x - cameraX, y = e.y;
  if (x < -TILE*2 || x > W/scale + TILE*2) return;
  // Body
  ctx.fillStyle = COLORS.goomba;
  ctx.beginPath(); ctx.ellipse(x+14, y+14, 14, 12, 0, 0, Math.PI*2); ctx.fill();
  // Feet
  ctx.fillStyle = COLORS.goombaDark;
  ctx.fillRect(x+2, y+22, 10, 6);
  ctx.fillRect(x+16, y+22, 10, 6);
  // Eyes
  ctx.fillStyle = '#fff';
  ctx.fillRect(x+6, y+8, 6, 7);
  ctx.fillRect(x+16, y+8, 6, 7);
  ctx.fillStyle = '#000';
  ctx.fillRect(x+8, y+10, 3, 4);
  ctx.fillRect(x+18, y+10, 3, 4);
  // Brow
  ctx.fillStyle = '#000';
  ctx.fillRect(x+5, y+7, 8, 2);
  ctx.fillRect(x+15, y+7, 8, 2);
}

function drawBackground() {
  // Sky
  ctx.fillStyle = COLORS.sky;
  ctx.fillRect(0, 0, W, H);

  // Clouds
  const clouds = [[8,2],[19,1],[35,2],[48,1],[60,3],[75,1],[90,2],[108,1]];
  ctx.fillStyle = COLORS.cloud;
  clouds.forEach(([cx, cy]) => {
    const x = cx*TILE - cameraX, y = cy*TILE;
    ctx.beginPath();
    ctx.ellipse(x, y+12, 20, 12, 0, 0, Math.PI*2); ctx.fill();
    ctx.ellipse(x+20, y+8, 16, 14, 0, 0, Math.PI*2); ctx.fill();
    ctx.ellipse(x+38, y+12, 18, 12, 0, 0, Math.PI*2); ctx.fill();
  });

  // Hills
  ctx.fillStyle = COLORS.hill;
  [[0,3],[16,2],[40,3],[65,2],[95,3]].forEach(([hx, hw]) => {
    const x = hx*TILE - cameraX, w = hw*TILE*2;
    ctx.beginPath(); ctx.moveTo(x, 12*TILE); ctx.quadraticCurveTo(x+w/2, 12*TILE-w*0.4, x+w, 12*TILE); ctx.fill();
  });

  // Bushes
  ctx.fillStyle = COLORS.bush;
  [[11,1],[30,2],[50,1],[72,2],[100,1]].forEach(([bx, bw]) => {
    const x = bx*TILE - cameraX, y = 11.3*TILE;
    for (let i = 0; i < bw; i++) {
      ctx.beginPath(); ctx.ellipse(x+i*20+10, y, 14, 10, 0, 0, Math.PI*2); ctx.fill();
    }
  });
}

function drawParticles() {
  particles.forEach(p => {
    const x = p.x - cameraX;
    if (p.type === 'coin') {
      ctx.fillStyle = COLORS.coin;
      ctx.fillRect(x, p.y, 12, 14);
      ctx.fillStyle = '#fff';
      ctx.fillRect(x+4, p.y+2, 4, 10);
    } else if (p.type === 'debris') {
      ctx.fillStyle = COLORS.brick;
      ctx.fillRect(x, p.y, 8, 8);
    } else if (p.type === 'squash') {
      ctx.fillStyle = COLORS.goomba;
      ctx.fillRect(x, p.y+20, 28, 6);
    }
  });
}

function draw() {
  ctx.save();
  ctx.scale(scale, scale);
  drawBackground();
  // Tiles
  const startTx = Math.max(0, Math.floor(cameraX / TILE) - 1);
  const endTx = Math.min(LEVEL_W, startTx + Math.ceil(W / (TILE * scale)) + 3);
  for (let ty = 0; ty < LEVEL_H; ty++) {
    for (let tx = startTx; tx < endTx; tx++) {
      if (level[ty][tx]) drawTile(tx, ty, level[ty][tx]);
    }
  }
  // Enemies
  enemies.forEach(e => { if (e.alive) drawGoomba(e); });
  // Mario
  if (!mario.dead) drawMario();
  // Particles
  drawParticles();
  // Flag pole at end
  const flagX = 113*TILE - cameraX;
  ctx.fillStyle = '#0f0'; ctx.fillRect(flagX+14, 3*TILE, 4, 9*TILE);
  ctx.fillStyle = '#f00'; ctx.fillRect(flagX+18, 3*TILE, 16, 16);
  ctx.restore();
}

// === Game Loop ===
function loop() {
  update();
  draw();
  requestAnimationFrame(loop);
}

function restartGame() {
  mario.x = 3*TILE; mario.y = 10*TILE; mario.vx = 0; mario.vy = 0; mario.dead = false; mario.dir = 1;
  score = 0; coins = 0; timer = 400; cameraX = 0; timerAcc = 0;
  enemies.forEach(e => { e.alive = true; e.x = e._ox || e.x; e.y = e._oy || e.y; });
  questionHit.clear();
  // rebuild level bricks
  [[20,8],[24,8],[77,8],[78,8],[79,4],[80,4],[81,4],[82,4],[83,4],[84,4],[85,4],[86,4]].forEach(([x,y]) => level[y][x] = 2);
  particles = [];
  document.getElementById('game-over').classList.add('hidden');
  document.getElementById('game-over').querySelector('h1').textContent = 'GAME OVER';
  gameState = 'play';
}

// Save original enemy positions
enemies.forEach(e => { e._ox = e.x; e._oy = e.y; });

loop();
