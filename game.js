// 3D Platformer Game in Three.js
class Game {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 50);
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true });
        
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setClearColor(0x87CEEB); // Sky blue
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        // Game state
        this.score = 0;
        this.lives = 3;
        this.level = 1;
        this.gameState = 'playing';
        
        // Input
        this.keys = {};
        this.touchControls = {};
        
        // Game objects
        this.player = null;
        this.platforms = [];
        this.coins = [];
        this.particles = [];
        
        // Physics
        this.gravity = 0.008;
        this.jumpVelocity = 0.22;
        
        // Camera
        this.cameraTarget = new THREE.Vector3();
        this.cameraPosition = new THREE.Vector3(0, 3, 6);
        
        // Timing
        this.lastTime = performance.now();
        this.coinRotation = 0;
        
        // Sound system
        this.audioContext = null;
        this.setupAudio();
        
        // Gyroscope system - DISABLED for now due to compatibility issues
        this.gyroEnabled = false;
        this.deviceOrientation = { alpha: 0, beta: 0, gamma: 0 };
        this.baseOrientation = { alpha: 0, beta: 0, gamma: 0 };
        this.gyroSupported = false; // Disabled
        
        this.init();
    }
    
    setupAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('Audio system initialized');
        } catch (e) {
            console.log('Audio not supported');
        }
    }
    
    setupGyroscope() {
        // Check if device orientation is supported
        if (window.DeviceOrientationEvent) {
            this.gyroSupported = true;
            
            // Add gyroscope toggle button listener
            const gyroToggle = document.getElementById('gyro-toggle');
            gyroToggle.addEventListener('click', () => this.toggleGyroscope());
            
            // Device orientation event listener
            window.addEventListener('deviceorientation', (event) => {
                if (this.gyroEnabled) {
                    this.deviceOrientation = {
                        alpha: event.alpha || 0,  // Z axis rotation (compass)
                        beta: event.beta || 0,    // X axis rotation (front-back tilt)
                        gamma: event.gamma || 0   // Y axis rotation (left-right tilt)
                    };
                }
            });
            
            console.log('Gyroscope support detected');
        } else {
            console.log('Gyroscope not supported on this device');
            // Hide gyro button if not supported
            const gyroToggle = document.getElementById('gyro-toggle');
            if (gyroToggle) gyroToggle.style.display = 'none';
        }
    }
    
    async toggleGyroscope() {
        if (!this.gyroSupported) return;
        
        const gyroToggle = document.getElementById('gyro-toggle');
        
        if (!this.gyroEnabled) {
            // Request permission on iOS devices
            if (typeof DeviceOrientationEvent.requestPermission === 'function') {
                try {
                    const permission = await DeviceOrientationEvent.requestPermission();
                    if (permission !== 'granted') {
                        console.log('Gyroscope permission denied');
                        return;
                    }
                } catch (error) {
                    console.log('Error requesting gyroscope permission:', error);
                    return;
                }
            }
            
            // Enable gyroscope
            this.gyroEnabled = true;
            this.baseOrientation = { ...this.deviceOrientation };
            gyroToggle.textContent = '🎯 Gyro: ON';
            gyroToggle.classList.add('enabled');
            console.log('Gyroscope enabled');
        } else {
            // Disable gyroscope
            this.gyroEnabled = false;
            gyroToggle.textContent = '🎯 Gyro: OFF';
            gyroToggle.classList.remove('enabled');
            console.log('Gyroscope disabled');
        }
    }
    
    playSound(frequency, duration, volume = 0.3) {
        if (!this.audioContext) return;
        
        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
            oscillator.type = 'sine';
            
            // Envelope for smooth sound
            gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(volume, this.audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + duration);
            
            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + duration);
            
        } catch (e) {
            console.log('Sound playback failed:', e);
        }
    }
    
    playJumpSound() {
        this.playSound(523, 0.1, 0.3); // C5 note
        console.log('Jump sound played');
    }
    
    playCoinSound() {
        this.playSound(784, 0.15, 0.4); // G5 note
        console.log('Coin sound played');
    }
    
    playDeathSound() {
        // Descending sound for death
        if (!this.audioContext) return;
        
        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            // Descending frequency
            oscillator.frequency.setValueAtTime(300, this.audioContext.currentTime);
            oscillator.frequency.linearRampToValueAtTime(150, this.audioContext.currentTime + 0.3);
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.4, this.audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + 0.3);
            
            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + 0.3);
            
            console.log('Death sound played');
        } catch (e) {
            console.log('Death sound failed:', e);
        }
    }
    
    init() {
        this.setupLighting();
        this.setupControls();
        // this.setupGyroscope(); // DISABLED - not working reliably
        this.loadLevel(1);
        this.updateUI();
        this.animate();
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Hide gyro toggle since it's disabled
        const gyroToggle = document.getElementById('gyro-toggle');
        if (gyroToggle) gyroToggle.style.display = 'none';
        
        console.log('3D Platformer Game Started!');
    }
    
    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
        this.scene.add(ambientLight);
        
        // Directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -10;
        directionalLight.shadow.camera.right = 10;
        directionalLight.shadow.camera.top = 10;
        directionalLight.shadow.camera.bottom = -10;
        this.scene.add(directionalLight);
    }
    
    setupControls() {
        // Keyboard controls
        document.addEventListener('keydown', (event) => {
            this.keys[event.code] = true;
            this.resumeAudio(); // Enable audio on first interaction
        });
        
        document.addEventListener('keyup', (event) => {
            this.keys[event.code] = false;
        });
        
        // Touch controls
        const touchButtons = document.querySelectorAll('.control-btn');
        
        touchButtons.forEach(button => {
            const key = button.dataset.key;
            
            // Touch start
            button.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.touchControls[key] = true;
                button.classList.add('active');
                this.resumeAudio(); // Enable audio on first interaction
            });
            
            // Touch end
            button.addEventListener('touchend', (e) => {
                e.preventDefault();
                this.touchControls[key] = false;
                button.classList.remove('active');
            });
            
            // Mouse events for desktop testing
            button.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.touchControls[key] = true;
                button.classList.add('active');
                this.resumeAudio(); // Enable audio on first interaction
            });
            
            button.addEventListener('mouseup', (e) => {
                e.preventDefault();
                this.touchControls[key] = false;
                button.classList.remove('active');
            });
        });
        
        // Prevent context menu on long press
        document.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    
    resumeAudio() {
        if (this.audioContext && this.audioContext.state === 'suspended') {
            this.audioContext.resume().then(() => {
                console.log('Audio context resumed');
            });
        }
    }
    
    isKeyPressed(key) {
        // Check both keyboard and touch controls
        switch(key) {
            case 'up': return this.keys['KeyW'] || this.keys['ArrowUp'] || this.touchControls['up'];
            case 'down': return this.keys['KeyS'] || this.keys['ArrowDown'] || this.touchControls['down'];
            case 'left': return this.keys['KeyA'] || this.keys['ArrowLeft'] || this.touchControls['left'];
            case 'right': return this.keys['KeyD'] || this.keys['ArrowRight'] || this.touchControls['right'];
            case 'jump': return this.keys['Space'] || this.keys['ShiftLeft'] || this.keys['ShiftRight'] || this.touchControls['jump'];
            case 'restart': return this.keys['KeyR'];
            default: return false;
        }
    }
    
    createPlayer() {
        const geometry = new THREE.BoxGeometry(0.5, 0.5, 0.5);
        const material = new THREE.MeshLambertMaterial({ color: 0xcc3333 });
        const player = new THREE.Mesh(geometry, material);
        
        player.position.set(0, 1, 0);
        player.castShadow = true;
        player.receiveShadow = true;
        
        // Player physics properties
        player.velocity = new THREE.Vector3(0, 0, 0);
        player.onGround = false;
        player.jumpBufferTimer = 0;
        player.coyoteTimer = 0;
        player.wasOnGround = false;
        
        this.scene.add(player);
        return player;
    }
    
    createPlatform(x, y, z, width, height, depth, color = 0x22aa22) {
        const geometry = new THREE.BoxGeometry(width, height, depth);
        const material = new THREE.MeshLambertMaterial({ color });
        const platform = new THREE.Mesh(geometry, material);
        
        platform.position.set(x, y, z);
        platform.castShadow = true;
        platform.receiveShadow = true;
        
        // Add wireframe edges
        const edges = new THREE.EdgesGeometry(geometry);
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x000000 }));
        platform.add(line);
        
        this.scene.add(platform);
        return platform;
    }
    
    createCoin(x, y, z) {
        const geometry = new THREE.BoxGeometry(0.3, 0.3, 0.3);
        const material = new THREE.MeshLambertMaterial({ color: 0xffdd00 });
        const coin = new THREE.Mesh(geometry, material);
        
        coin.position.set(x, y, z);
        coin.castShadow = true;
        
        this.scene.add(coin);
        return coin;
    }
    
    createShadow(player) {
        const geometry = new THREE.CircleGeometry(0.3, 12);
        const material = new THREE.MeshBasicMaterial({ 
            color: 0x000000, 
            transparent: true, 
            opacity: 0.5 
        });
        const shadow = new THREE.Mesh(geometry, material);
        shadow.rotation.x = -Math.PI / 2; // Rotate to lay flat
        shadow.visible = false;
        
        this.scene.add(shadow);
        return shadow;
    }
    
    loadLevel(levelNum) {
        // Clear existing level - FIX: properly remove platform meshes
        this.platforms.forEach(platform => this.scene.remove(platform.mesh));
        this.coins.forEach(coin => this.scene.remove(coin));
        
        this.platforms = [];
        this.coins = [];
        
        // Create player if doesn't exist
        if (!this.player) {
            this.player = this.createPlayer();
            this.shadow = this.createShadow();
        } else {
            this.resetPlayer();
        }
        
        const levels = {
            1: {
                // Tutorial level - simple jumps
                platforms: [
                    [0, -0.5, 0, 4, 0.5, 4, 0x1a5c1a],      // Base
                    [0, -0.2, -2, 1.5, 0.3, 1.5, 0x22aa22],
                    [2, 0.2, -2, 1, 0.3, 1, 0x22aa22],
                    [3, 0.6, 0, 1, 0.3, 1, 0x22aa22],
                    [2, 1.0, 2, 1, 0.3, 1, 0x22aa22],
                    [0, 1.4, 3, 1.5, 0.3, 1.5, 0x22aa22],
                    [-2, 1.8, 2, 1, 0.3, 1, 0x22aa22],
                ],
                coins: [
                    [0, 0.5, -2], [2, 0.9, -2], [3, 1.3, 0],
                    [2, 1.7, 2], [0, 2.1, 3], [-2, 2.5, 2]
                ]
            },
            2: {
                // Precision jumping
                platforms: [
                    [0, -0.5, 0, 4, 0.5, 4, 0x1a5c1a],
                    [1, -0.2, -3, 1, 0.2, 1, 0x2222aa],
                    [3, 0.1, -2, 1, 0.2, 1, 0x2222aa],
                    [4, 0.5, 0, 1, 0.2, 1, 0x2222aa],
                    [3, 0.9, 2, 1, 0.2, 1, 0x2222aa],
                    [1, 1.3, 3, 1, 0.2, 1, 0x2222aa],
                    [-1, 1.7, 3, 1, 0.2, 1, 0x2222aa],
                    [-3, 2.1, 2, 1, 0.2, 1, 0x2222aa],
                    [-4, 2.5, 0, 1, 0.2, 1, 0x2222aa],
                    [-3, 2.9, -2, 1, 0.2, 1, 0x2222aa],
                    [-1, 3.3, -3, 2, 0.2, 2, 0x2222aa],
                ],
                coins: [
                    [1, 0.5, -3], [3, 0.8, -2], [4, 1.2, 0], [3, 1.6, 2],
                    [1, 2.0, 3], [-1, 2.4, 3], [-3, 2.8, 2], [-4, 3.2, 0],
                    [-3, 3.6, -2], [-1, 4.0, -3]
                ]
            },
            3: {
                // Spiral tower
                platforms: [
                    [0, -0.5, 0, 3, 0.5, 3, 0x1a5c1a],
                    [2, 0.0, 0, 1, 0.2, 1, 0xaa2222],
                    [2, 0.4, -2, 1, 0.2, 1, 0xaa2222],
                    [0, 0.8, -3, 1, 0.2, 1, 0xaa2222],
                    [-2, 1.2, -2, 1, 0.2, 1, 0xaa2222],
                    [-3, 1.6, 0, 1, 0.2, 1, 0xaa2222],
                    [-2, 2.0, 2, 1, 0.2, 1, 0xaa2222],
                    [0, 2.4, 3, 1, 0.2, 1, 0xaa2222],
                    [2, 2.8, 2, 1, 0.2, 1, 0xaa2222],
                    [3, 3.2, 0, 1, 0.2, 1, 0xaa2222],
                    [2, 3.6, -1, 1, 0.2, 1, 0xaa2222],
                    [0, 4.0, -2, 2, 0.2, 2, 0xaa2222],
                ],
                coins: [
                    [2, 0.7, 0], [2, 1.1, -2], [0, 1.5, -3], [-2, 1.9, -2],
                    [-3, 2.3, 0], [-2, 2.7, 2], [0, 3.1, 3], [2, 3.5, 2],
                    [3, 3.9, 0], [2, 4.3, -1], [0, 4.7, -2]
                ]
            },
            4: {
                // Long jumps and gaps
                platforms: [
                    [0, -0.5, 0, 2, 0.5, 2, 0x1a5c1a],
                    [4, 0.0, 0, 1.5, 0.3, 1.5, 0xaaaa22],
                    [8, 0.3, -1, 1, 0.3, 1, 0xaaaa22],
                    [6, 0.8, -4, 1, 0.3, 1, 0xaaaa22],
                    [2, 1.2, -5, 1, 0.3, 1, 0xaaaa22],
                    [-2, 1.6, -4, 1, 0.3, 1, 0xaaaa22],
                    [-5, 2.0, -1, 1, 0.3, 1, 0xaaaa22],
                    [-7, 2.4, 2, 1, 0.3, 1, 0xaaaa22],
                    [-4, 2.8, 5, 1, 0.3, 1, 0xaaaa22],
                    [0, 3.2, 6, 1, 0.3, 1, 0xaaaa22],
                    [4, 3.6, 4, 1, 0.3, 1, 0xaaaa22],
                    [7, 4.0, 1, 1.5, 0.3, 1.5, 0xaaaa22],
                ],
                coins: [
                    [4, 0.7, 0], [8, 1.0, -1], [6, 1.5, -4], [2, 1.9, -5],
                    [-2, 2.3, -4], [-5, 2.7, -1], [-7, 3.1, 2], [-4, 3.5, 5],
                    [0, 3.9, 6], [4, 4.3, 4], [7, 4.7, 1]
                ]
            },
            5: {
                // Moving maze
                platforms: [
                    [0, -0.5, 0, 2, 0.5, 2, 0x1a5c1a],
                    [3, 0.0, 0, 1, 0.2, 3, 0xaaaaaa],
                    [1, 0.4, 3, 3, 0.2, 1, 0xaaaaaa],
                    [-1, 0.8, 5, 1, 0.2, 1, 0xaaaaaa],
                    [-4, 1.2, 4, 1, 0.2, 3, 0xaaaaaa],
                    [-6, 1.6, 1, 3, 0.2, 1, 0xaaaaaa],
                    [-4, 2.0, -1, 1, 0.2, 1, 0xaaaaaa],
                    [-1, 2.4, -2, 1, 0.2, 3, 0xaaaaaa],
                    [2, 2.8, -1, 1, 0.2, 1, 0xaaaaaa],
                    [5, 3.2, 0, 1, 0.2, 3, 0xaaaaaa],
                    [3, 3.6, 3, 3, 0.2, 1, 0xaaaaaa],
                    [0, 4.0, 5, 1, 0.2, 1, 0xaaaaaa],
                    [-3, 4.4, 3, 1, 0.2, 1, 0xaaaaaa],
                    [-5, 4.8, 0, 1, 0.2, 1, 0xaaaaaa],
                    [-2, 5.2, -2, 3, 0.2, 1, 0xaaaaaa],
                ],
                coins: [
                    [3, 0.7, 1], [1, 1.1, 3], [-1, 1.5, 5], [-4, 1.9, 3],
                    [-6, 2.3, 1], [-4, 2.7, -1], [-1, 3.1, -1], [2, 3.5, -1],
                    [5, 3.9, 1], [3, 4.3, 3], [0, 4.7, 5], [-3, 5.1, 3],
                    [-5, 5.5, 0], [-2, 5.9, -2]
                ]
            }
        };
        
        const currentLevel = levels[levelNum];
        if (!currentLevel) return;
        
        // Create platforms
        currentLevel.platforms.forEach(([x, y, z, w, h, d, color]) => {
            const platform = this.createPlatform(x, y, z, w, h, d, color);
            this.platforms.push({ mesh: platform, x, y, z, width: w, height: h, depth: d });
        });
        
        // Create coins
        currentLevel.coins.forEach(([x, y, z]) => {
            const coin = this.createCoin(x, y, z);
            this.coins.push(coin);
        });
        
        this.level = levelNum;
        this.updateUI();
    }
    
    resetPlayer() {
        this.player.position.set(0, 1, 0);
        this.player.velocity.set(0, 0, 0);
        this.player.onGround = false;
        this.player.jumpBufferTimer = 0;
        this.player.coyoteTimer = 0;
    }
    
    updatePlayer(deltaTime) {
        const player = this.player;
        const vel = player.velocity;
        
        // Store previous ground state
        player.wasOnGround = player.onGround;
        
        // Update timers
        if (player.coyoteTimer > 0) player.coyoteTimer -= deltaTime;
        if (player.jumpBufferTimer > 0) player.jumpBufferTimer -= deltaTime;
        
        // Apply gravity
        if (!player.onGround) {
            vel.y -= this.gravity;
        }
        
        // Handle input
        const moveDir = new THREE.Vector2(0, 0);
        
        if (this.isKeyPressed('up')) moveDir.y -= 1;
        if (this.isKeyPressed('down')) moveDir.y += 1;
        if (this.isKeyPressed('left')) moveDir.x -= 1;
        if (this.isKeyPressed('right')) moveDir.x += 1;
        
        // Normalize movement
        if (moveDir.length() > 0) {
            moveDir.normalize();
            vel.x += moveDir.x * 0.006;
            vel.z += moveDir.y * 0.006;
        }
        
        // Jump
        if (this.isKeyPressed('jump') && player.jumpBufferTimer <= 0 && 
            (player.onGround || player.coyoteTimer > 0)) {
            vel.y = this.jumpVelocity;
            player.onGround = false;
            player.coyoteTimer = 0;
            player.jumpBufferTimer = 0.1;
            console.log('Jump!');
            this.playJumpSound();
        }
        
        // Apply friction
        vel.x *= 0.88;
        vel.z *= 0.88;
        
        // Limit speed
        const horizontalSpeed = Math.sqrt(vel.x * vel.x + vel.z * vel.z);
        if (horizontalSpeed > 0.1) {
            vel.x = (vel.x / horizontalSpeed) * 0.1;
            vel.z = (vel.z / horizontalSpeed) * 0.1;
        }
        
        // Update position
        player.position.add(vel);
        
        // Check collisions
        this.checkCollisions(player);
        
        // Coyote time
        if (player.wasOnGround && !player.onGround) {
            player.coyoteTimer = 0.12;
        }
        
        // Reset if fallen
        if (player.position.y < -10) {
            this.lives--;
            console.log(`Life lost! Lives remaining: ${this.lives}`);
            
            if (this.lives <= 0) {
                console.log(`Game Over! Final Score: ${this.score}`);
                this.restartGame();
            } else {
                this.resetPlayer();
            }
            this.updateUI();
            this.playDeathSound();
        }
    }
    
    checkCollisions(player) {
        player.onGround = false;
        
        for (let platform of this.platforms) {
            const px = platform.x, py = platform.y, pz = platform.z;
            const pw = platform.width, ph = platform.height, pd = platform.depth;
            
            // AABB collision detection
            if (Math.abs(player.position.x - px) < pw/2 + 0.25 &&
                Math.abs(player.position.z - pz) < pd/2 + 0.25 &&
                player.position.y - 0.25 <= py + ph/2 &&
                player.position.y - 0.25 > py + ph/2 - 0.2 &&
                player.velocity.y <= 0) {
                
                player.position.y = py + ph/2 + 0.25;
                player.velocity.y = 0;
                player.onGround = true;
                player.coyoteTimer = 0;
                break;
            }
        }
    }
    
    updateCoins(deltaTime) {
        this.coinRotation += 120 * deltaTime * Math.PI / 180;
        
        // Rotate coins
        this.coins.forEach(coin => {
            coin.rotation.y = this.coinRotation;
            coin.position.y += Math.sin(coin.rotation.y * 0.1) * 0.001;
        });
        
        // Check coin collection
        for (let i = this.coins.length - 1; i >= 0; i--) {
            const coin = this.coins[i];
            const distance = this.player.position.distanceTo(coin.position);
            
            if (distance < 0.4) {
                this.scene.remove(coin);
                this.coins.splice(i, 1);
                this.score += 100;
                console.log(`Coin collected! Score: ${this.score}`);
                this.updateUI();
                this.playCoinSound();
            }
        }
        
        // Check level completion
        if (this.coins.length === 0) {
            const levelBonus = 500 * this.level;
            this.score += levelBonus;
            console.log(`Level ${this.level} Complete! Bonus: ${levelBonus}`);
            this.nextLevel();
        }
    }
    
    updateShadow() {
        if (!this.shadow) return;
        
        if (this.player.onGround) {
            this.shadow.visible = false;
            return;
        }
        
        // Find ground below player
        let groundY = -10;
        
        for (let platform of this.platforms) {
            const px = platform.x, py = platform.y, pz = platform.z;
            const pw = platform.width, pd = platform.depth, ph = platform.height;
            
            if (Math.abs(this.player.position.x - px) < pw/2 + 0.5 &&
                Math.abs(this.player.position.z - pz) < pd/2 + 0.5 &&
                py + ph/2 < this.player.position.y) {
                groundY = Math.max(groundY, py + ph/2);
            }
        }
        
        const heightAboveGround = this.player.position.y - groundY;
        
        if (heightAboveGround < 0.1) {
            this.shadow.visible = false;
            return;
        }
        
        this.shadow.visible = true;
        this.shadow.position.set(this.player.position.x, groundY + 0.01, this.player.position.z);
        
        // Adjust shadow properties based on height
        const opacity = Math.max(0.3, Math.min(0.8, 1.0 - heightAboveGround / 3.0));
        const scale = Math.min(1.5, 1.0 + heightAboveGround * 0.2);
        
        this.shadow.material.opacity = opacity;
        this.shadow.scale.set(scale, 1, scale);
    }
    
    updateCamera() {
        if (this.gyroEnabled && this.gyroSupported) {
            // Gyroscope-controlled camera
            const sensitivity = 0.5;
            
            // Calculate relative rotation from base orientation
            const deltaAlpha = (this.deviceOrientation.alpha - this.baseOrientation.alpha) * Math.PI / 180;
            const deltaBeta = (this.deviceOrientation.beta - this.baseOrientation.beta) * Math.PI / 180;
            const deltaGamma = (this.deviceOrientation.gamma - this.baseOrientation.gamma) * Math.PI / 180;
            
            // Calculate camera position using spherical coordinates around player
            const distance = 8;
            const height = 3;
            
            // Use gamma for horizontal rotation (left-right tilt)
            const horizontalAngle = deltaGamma * sensitivity;
            // Use beta for vertical rotation (front-back tilt), clamped
            const verticalAngle = Math.max(-Math.PI/3, Math.min(Math.PI/6, deltaBeta * sensitivity));
            
            // Calculate camera position
            const x = this.player.position.x + distance * Math.cos(verticalAngle) * Math.sin(horizontalAngle);
            const y = this.player.position.y + height + distance * Math.sin(verticalAngle);
            const z = this.player.position.z + distance * Math.cos(verticalAngle) * Math.cos(horizontalAngle);
            
            this.camera.position.set(x, y, z);
            this.camera.lookAt(this.player.position);
            
        } else {
            // Standard smooth camera follow
            this.cameraTarget.set(
                this.player.position.x + 4,
                this.player.position.y + 3,
                this.player.position.z + 5
            );
            
            this.cameraPosition.lerp(this.cameraTarget, 0.08);
            this.camera.position.copy(this.cameraPosition);
            this.camera.lookAt(this.player.position);
        }
    }
    
    updateUI() {
        document.getElementById('score').textContent = this.score;
        document.getElementById('level').textContent = this.level;
        document.getElementById('lives').textContent = this.lives;
        document.getElementById('coins').textContent = this.coins.length;
    }
    
    nextLevel() {
        if (this.level < 5) {
            this.loadLevel(this.level + 1);
            console.log(`Starting Level ${this.level}`);
        } else {
            console.log('🎉 CONGRATULATIONS! You completed ALL 5 levels! 🎉');
            console.log(`Final Score: ${this.score}`);
            this.loadLevel(1);
            console.log('Restarting from Level 1...');
        }
    }
    
    restartGame() {
        this.score = 0;
        this.lives = 3;
        this.loadLevel(1);
        console.log('Game restarted!');
    }
    
    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        const currentTime = performance.now();
        const deltaTime = Math.min((currentTime - this.lastTime) / 1000, 1/30);
        this.lastTime = currentTime;
        
        if (this.gameState === 'playing') {
            this.updatePlayer(deltaTime);
            this.updateCoins(deltaTime);
            this.updateShadow();
            this.updateCamera();
            
            // Handle restart
            if (this.isKeyPressed('restart')) {
                this.resetPlayer();
            }
        }
        
        this.renderer.render(this.scene, this.camera);
    }
}

// Start the game when page loads
window.addEventListener('load', () => {
    new Game();
}); 