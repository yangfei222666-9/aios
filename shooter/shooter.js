// Space Shooter - Game Engine
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');

let W = 600, H = 800;
function resize() {
  const maxW = Math.min(window.innerWidth, 600);
  const maxH = Math.min(window.innerHeight, 800);
  const aspect = 600 / 800;
  if (maxW / maxH > aspect) { H = maxH; W = H * aspect; }
  else { W = maxW; H = W / aspect; }
  canvas.width = W; canvas.height = H;
}
resize();
window.addEventListener('resize', resize);

// === State ===
let state = 'start'; // start | play | over
let score = 0, lives = 3, wave = 1;
let shootCooldown = 0, invincible = 0;
let starField = [];
let shakeTimer = 0, shakeX = 0, shakeY = 0;

// === Stars ===
for (let i = 0; i < 120; i++) {
  starField.push({ x: Math.random() * 600, y: Math.random() * 800, s: Math.random() * 2 + 0.5, b: Math.random() });
}

// === Player ===
const player = { x: 300, y: 700, w: 36, h: 40, speed: 5 };

// === Bullets ===
let bullets = [];
let enemyBullets = [];
let enemies = [];
let explosions = [];
let powerups = [];

// === Input ===
const keys = {};
window.addEventListener('keydown', e => {
  keys[e.code] = true;
  if (state === 'start') startGame();
  if (state === 'over') startGame();
});
window.addEventListener('keyup', e => keys[e.code] = false);

// Touch
const touchMap = { 'btn-left': 'ArrowLeft', 'btn-right': 'ArrowRight', 'btn-up': 'ArrowUp', 'btn-fire': 'Space' };
Object.entries(touchMap).forEach(([id, code]) => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('touchstart', e => { e.preventDefault(); keys[code] = true; if (state !== 'play') startGame(); });
  el.addEventListener('touchend', e => { e.preventDefault(); keys[code] = false; });
});
document.addEventListener('touchstart', () => { if (state === 'start') startGame(); });

// === Enemy Patterns ===
function spawnWave(w) {
  enemies = [];
  const rows = Math.min(3 + Math.floor(w / 2), 6);
  const cols = Math.min(5 + Math.floor(w / 3), 10);
  const hp = 1 + Math.floor(w / 3);
  const shootRate = Math.max(0.001, 0.003 + w * 0.001);

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const type = r === 0 ? 2 : r < 2 ? 1 : 0;
      enemies.push({
        x: 60 + c * 52, y: 60 + r * 48,
        w: 32, h: 32,
        type, hp: type === 2 ? hp + 1 : hp,
        maxHp: type === 2 ? hp + 1 : hp,
        alive: true,
        shootRate,
        moveTimer: Math.random() * Math.PI * 2,
        baseX: 60 + c * 52,
      });
    }
  }
}

// === Helpers ===
function overlap(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function addExplosion(x, y, size) {
  for (let i = 0; i < size; i++) {
    const angle = Math.random() * Math.PI * 2;
    const speed = Math.random() * 3 + 1;
    explosions.push({
      x, y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      life: 20 + Math.random() * 15,
      maxLife: 35,
      r: Math.random() * 3 + 1,
      color: Math.random() > 0.5 ? '#ff4' : Math.random() > 0.5 ? '#f84' : '#f44',
    });
  }
}

function shake(t) { shakeTimer = t; }

// === Update ===
function update() {
  if (state !== 'play') return;

  // Player movement
  if (keys['ArrowLeft'] || keys['KeyA']) player.x -= player.speed;
  if (keys['ArrowRight'] || keys['KeyD']) player.x += player.speed;
  if (keys['ArrowUp'] || keys['KeyW']) player.y -= player.speed;
  if (keys['ArrowDown'] || keys['KeyS']) player.y += player.speed;
  player.x = Math.max(0, Math.min(W - player.w, player.x));
  player.y = Math.max(H * 0.4, Math.min(H - player.h - 10, player.y));

  // Shoot
  shootCooldown--;
  if ((keys['Space'] || keys['KeyZ']) && shootCooldown <= 0) {
    bullets.push({ x: player.x + player.w / 2 - 2, y: player.y - 8, w: 4, h: 12, vy: -8 });
    shootCooldown = 8;
  }

  // Bullets
  bullets.forEach(b => b.y += b.vy);
  bullets = bullets.filter(b => b.y > -20);

  // Enemy bullets
  enemyBullets.forEach(b => { b.y += b.vy; b.x += b.vx || 0; });
  enemyBullets = enemyBullets.filter(b => b.y < H + 20 && b.x > -20 && b.x < W + 20);

  // Enemy movement
  const t = Date.now() / 1000;
  enemies.forEach(e => {
    if (!e.alive) return;
    e.moveTimer += 0.02;
    e.x = e.baseX + Math.sin(e.moveTimer) * 30;
    e.y += Math.sin(t * 0.5 + e.baseX) * 0.15;

    // Enemy shoot
    if (Math.random() < e.shootRate) {
      const dx = player.x - e.x, dy = player.y - e.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const speed = 3 + wave * 0.3;
      enemyBullets.push({
        x: e.x + e.w / 2 - 3, y: e.y + e.h,
        w: 6, h: 6,
        vx: (dx / dist) * speed * 0.3,
        vy: speed,
      });
    }
  });

  // Bullet-enemy collision
  bullets.forEach(b => {
    enemies.forEach(e => {
      if (!e.alive) return;
      if (overlap(b, e)) {
        b.y = -100; // remove
        e.hp--;
        if (e.hp <= 0) {
          e.alive = false;
          const pts = (e.type + 1) * 100;
          score += pts;
          addExplosion(e.x + e.w / 2, e.y + e.h / 2, 15 + e.type * 5);
          shake(5);
          // Power-up drop
          if (Math.random() < 0.1) {
            powerups.push({ x: e.x, y: e.y, w: 16, h: 16, vy: 1.5, type: Math.random() > 0.5 ? 'life' : 'rapid' });
          }
        } else {
          addExplosion(b.x, b.y, 4);
        }
      }
    });
  });

  // Enemy bullet - player collision
  if (invincible <= 0) {
    enemyBullets.forEach(b => {
      if (overlap(b, player)) {
        b.y = H + 100;
        lives--;
        invincible = 90;
        shake(10);
        addExplosion(player.x + player.w / 2, player.y + player.h / 2, 20);
        if (lives <= 0) {
          state = 'over';
          document.getElementById('overlay').classList.remove('hidden');
          document.getElementById('overlay').querySelector('h1').textContent = 'GAME OVER';
          document.getElementById('overlay').querySelector('.sub').textContent = `最终得分: ${score}`;
        }
      }
    });
  }
  if (invincible > 0) invincible--;

  // Powerups
  powerups.forEach(p => p.y += p.vy);
  powerups = powerups.filter(p => {
    if (p.y > H + 20) return false;
    if (overlap(p, player)) {
      if (p.type === 'life') { lives = Math.min(lives + 1, 5); }
      else if (p.type === 'rapid') { shootCooldown = -60; } // 60 frames rapid fire
      score += 50;
      return false;
    }
    return true;
  });

  // Explosions
  explosions.forEach(p => { p.x += p.vx; p.y += p.vy; p.life--; p.vx *= 0.97; p.vy *= 0.97; });
  explosions = explosions.filter(p => p.life > 0);

  // Screen shake
  if (shakeTimer > 0) {
    shakeTimer--;
    shakeX = (Math.random() - 0.5) * shakeTimer * 1.5;
    shakeY = (Math.random() - 0.5) * shakeTimer * 1.5;
  } else { shakeX = 0; shakeY = 0; }

  // Next wave
  if (enemies.every(e => !e.alive)) {
    wave++;
    spawnWave(wave);
    enemyBullets = [];
  }

  // UI
  document.getElementById('score').textContent = String(score).padStart(6, '0');
  document.getElementById('wave').textContent = wave;
  document.getElementById('lives').textContent = '♥'.repeat(lives);
}

// === Draw ===
function drawStars() {
  starField.forEach(s => {
    s.y += s.s * 0.8;
    if (s.y > 800) { s.y = 0; s.x = Math.random() * 600; }
    const alpha = 0.3 + s.b * 0.7;
    ctx.fillStyle = `rgba(255,255,255,${alpha})`;
    ctx.fillRect(s.x * (W / 600), s.y * (H / 800), s.s, s.s);
  });
}

function drawPlayer() {
  if (invincible > 0 && Math.floor(invincible / 4) % 2 === 0) return;
  const x = player.x, y = player.y;
  // Body
  ctx.fillStyle = '#0af';
  ctx.beginPath();
  ctx.moveTo(x + player.w / 2, y);
  ctx.lineTo(x + player.w, y + player.h);
  ctx.lineTo(x, y + player.h);
  ctx.closePath();
  ctx.fill();
  // Cockpit
  ctx.fillStyle = '#0ff';
  ctx.beginPath();
  ctx.moveTo(x + player.w / 2, y + 10);
  ctx.lineTo(x + player.w / 2 + 6, y + player.h - 8);
  ctx.lineTo(x + player.w / 2 - 6, y + player.h - 8);
  ctx.closePath();
  ctx.fill();
  // Wings
  ctx.fillStyle = '#08c';
  ctx.fillRect(x - 4, y + player.h - 12, 10, 8);
  ctx.fillRect(x + player.w - 6, y + player.h - 12, 10, 8);
  // Engine glow
  ctx.fillStyle = `rgba(0,200,255,${0.3 + Math.random() * 0.3})`;
  ctx.beginPath();
  ctx.ellipse(x + player.w / 2, y + player.h + 4, 6, 8 + Math.random() * 6, 0, 0, Math.PI * 2);
  ctx.fill();
}

function drawEnemy(e) {
  const x = e.x, y = e.y;
  const hpRatio = e.hp / e.maxHp;
  if (e.type === 0) { // basic
    ctx.fillStyle = `rgb(${200 - hpRatio * 80},${60 + hpRatio * 40},${60 + hpRatio * 40})`;
    ctx.fillRect(x + 4, y + 4, e.w - 8, e.h - 8);
    ctx.fillRect(x, y + 8, e.w, e.h - 16);
    ctx.fillStyle = '#ff0';
    ctx.fillRect(x + 8, y + 12, 4, 4);
    ctx.fillRect(x + 20, y + 12, 4, 4);
  } else if (e.type === 1) { // medium
    ctx.fillStyle = `rgb(${180 - hpRatio * 60},${100 + hpRatio * 80},${50})`;
    ctx.beginPath();
    ctx.moveTo(x + e.w / 2, y);
    ctx.lineTo(x + e.w, y + e.h * 0.7);
    ctx.lineTo(x + e.w - 4, y + e.h);
    ctx.lineTo(x + 4, y + e.h);
    ctx.lineTo(x, y + e.h * 0.7);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = '#f80';
    ctx.fillRect(x + 10, y + 14, 5, 5);
    ctx.fillRect(x + 18, y + 14, 5, 5);
  } else { // boss-type
    ctx.fillStyle = `rgb(${140 + hpRatio * 60},${40},${180 + hpRatio * 40})`;
    ctx.beginPath();
    ctx.ellipse(x + e.w / 2, y + e.h / 2, e.w / 2, e.h / 2, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#f0f';
    ctx.beginPath();
    ctx.ellipse(x + e.w / 2, y + e.h / 2, e.w / 4, e.h / 4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.fillRect(x + 10, y + 12, 4, 6);
    ctx.fillRect(x + 18, y + 12, 4, 6);
  }
  // HP bar
  if (e.hp < e.maxHp) {
    ctx.fillStyle = '#300';
    ctx.fillRect(x, y - 6, e.w, 3);
    ctx.fillStyle = '#0f0';
    ctx.fillRect(x, y - 6, e.w * hpRatio, 3);
  }
}

function drawBullets() {
  ctx.fillStyle = '#0ff';
  ctx.shadowColor = '#0ff';
  ctx.shadowBlur = 6;
  bullets.forEach(b => {
    ctx.fillRect(b.x, b.y, b.w, b.h);
  });
  ctx.shadowBlur = 0;

  enemyBullets.forEach(b => {
    ctx.fillStyle = '#f44';
    ctx.shadowColor = '#f44';
    ctx.shadowBlur = 4;
    ctx.beginPath();
    ctx.arc(b.x + 3, b.y + 3, 3, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.shadowBlur = 0;
}

function drawPowerups() {
  powerups.forEach(p => {
    const glow = 0.5 + Math.sin(Date.now() / 200) * 0.3;
    if (p.type === 'life') {
      ctx.fillStyle = `rgba(255,80,80,${glow})`;
      ctx.font = '16px sans-serif';
      ctx.fillText('♥', p.x, p.y + 14);
    } else {
      ctx.fillStyle = `rgba(255,255,0,${glow})`;
      ctx.font = '14px sans-serif';
      ctx.fillText('⚡', p.x, p.y + 14);
    }
  });
}

function drawExplosions() {
  explosions.forEach(p => {
    const alpha = p.life / p.maxLife;
    ctx.globalAlpha = alpha;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r * (1 + (1 - alpha) * 2), 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
}

function draw() {
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, W, H);

  ctx.save();
  ctx.translate(shakeX, shakeY);

  drawStars();

  if (state === 'play' || state === 'over') {
    enemies.forEach(e => { if (e.alive) drawEnemy(e); });
    drawBullets();
    drawPowerups();
    drawExplosions();
    if (state === 'play') drawPlayer();
  }

  ctx.restore();
}

// === Game Loop ===
function loop() {
  update();
  draw();
  requestAnimationFrame(loop);
}

function startGame() {
  player.x = W / 2 - player.w / 2;
  player.y = H - 80;
  score = 0; lives = 3; wave = 1;
  bullets = []; enemyBullets = []; explosions = []; powerups = [];
  invincible = 60; shootCooldown = 0;
  spawnWave(1);
  state = 'play';
  document.getElementById('overlay').classList.add('hidden');
}

loop();
