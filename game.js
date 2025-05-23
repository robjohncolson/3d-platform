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
        this.thumbstick = {
            active: false,
            touchId: null, // Track which touch is controlling the thumbstick
            centerX: 0,
            centerY: 0,
            currentX: 0,
            currentY: 0,
            moveX: 0,
            moveY: 0,
            maxDistance: 35 // Maximum distance from center
        };
        
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
        
        // Gyroscope system - RE-ENABLED since it works well on mobile!
        this.gyroEnabled = false;
        this.deviceOrientation = { alpha: 0, beta: 0, gamma: 0 };
        this.baseOrientation = { alpha: 0, beta: 0, gamma: 0 };
        this.gyroSupported = false;
        
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
    
    createSynthSound(frequency, duration, volume = 0.3) {
        if (!this.audioContext) return null;
        
        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            const filterNode = this.audioContext.createBiquadFilter();
            
            // Connect the chain: oscillator -> filter -> gain -> destination
            oscillator.connect(filterNode);
            filterNode.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            // Set up oscillator
            oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
            oscillator.type = 'sine';
            
            // Set up filter for a more synth-like sound
            filterNode.type = 'lowpass';
            filterNode.frequency.setValueAtTime(frequency * 2, this.audioContext.currentTime);
            filterNode.Q.setValueAtTime(1, this.audioContext.currentTime);
            
            // Create an envelope with attack, sustain, and release
            const now = this.audioContext.currentTime;
            const attackTime = 0.01;
            const releaseTime = duration * 0.3;
            const sustainTime = duration - attackTime - releaseTime;
            
            // Envelope: quick attack, sustain, then exponential decay
            gainNode.gain.setValueAtTime(0, now);
            gainNode.gain.linearRampToValueAtTime(volume, now + attackTime);
            gainNode.gain.setValueAtTime(volume, now + attackTime + sustainTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, now + duration);
            
            return { oscillator, gainNode, duration };
            
        } catch (e) {
            console.log('Sound creation failed:', e);
            return null;
        }
    }
    
    playSound(frequency, duration, volume = 0.3) {
        const sound = this.createSynthSound(frequency, duration, volume);
        if (sound) {
            try {
                sound.oscillator.start(this.audioContext.currentTime);
                sound.oscillator.stop(this.audioContext.currentTime + sound.duration);
            } catch (e) {
                console.log('Sound playback failed:', e);
            }
        }
    }
    
    playJumpSound() {
        // Higher pitched, shorter for crisp jump sound
        this.playSound(523, 0.1, 0.4); // C5 note
        console.log('Jump sound played');
    }
    
    playCoinSound() {
        // Bright, pleasant coin collection sound
        this.playSound(880, 0.15, 0.5); // A5 note
        console.log('Coin sound played');
    }
    
    playDeathSound() {
        // Descending sound with more dramatic envelope
        if (!this.audioContext) return;
        
        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            const filterNode = this.audioContext.createBiquadFilter();
            
            oscillator.connect(filterNode);
            filterNode.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            // Descending frequency sweep
            const now = this.audioContext.currentTime;
            const duration = 0.4;
            
            oscillator.frequency.setValueAtTime(330, now);
            oscillator.frequency.linearRampToValueAtTime(165, now + duration);
            oscillator.type = 'sawtooth'; // More dramatic for death sound
            
            // Filter sweep
            filterNode.type = 'lowpass';
            filterNode.frequency.setValueAtTime(1000, now);
            filterNode.frequency.linearRampToValueAtTime(200, now + duration);
            filterNode.Q.setValueAtTime(2, now);
            
            // Dramatic envelope
            gainNode.gain.setValueAtTime(0, now);
            gainNode.gain.linearRampToValueAtTime(0.6, now + 0.02);
            gainNode.gain.exponentialRampToValueAtTime(0.001, now + duration);
            
            oscillator.start(now);
            oscillator.stop(now + duration);
            
            console.log('Death sound played');
        } catch (e) {
            console.log('Death sound failed:', e);
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
    
    init() {
        this.setupLighting();
        this.setupControls();
        this.setupGyroscope(); // RE-ENABLED - works great on mobile!
        this.loadLevel(1);
        this.updateUI();
        this.animate();
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
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
        
        // Thumbstick controls
        this.setupThumbstick();
        
        // Jump button
        const jumpButton = document.getElementById('jump');
        
        // Track jump button touch state
        this.jumpTouchId = null;
        
        // Touch events for jump button - improved for multitouch
        jumpButton.addEventListener('touchstart', (e) => {
            // Only handle if we don't already have a touch on this button
            if (this.jumpTouchId !== null) return;
            
            console.log('Jump button touch start:', e.type, e.touches?.length || 'mouse');
            this.jumpTouchId = e.touches[0].identifier;
            this.touchControls['jump'] = true;
            jumpButton.classList.add('active');
            this.resumeAudio();
            
            // Prevent default behaviors but don't stop propagation to avoid interfering with other touches
            if (e.preventDefault) e.preventDefault();
        }, { passive: false });
        
        jumpButton.addEventListener('touchend', (e) => {
            // Check if our specific touch ended
            let ourTouchEnded = false;
            for (let i = 0; i < e.changedTouches.length; i++) {
                if (e.changedTouches[i].identifier === this.jumpTouchId) {
                    ourTouchEnded = true;
                    break;
                }
            }
            
            if (ourTouchEnded) {
                this.jumpTouchId = null;
                this.touchControls['jump'] = false;
                jumpButton.classList.remove('active');
                console.log('Jump button touch end - our touch ended');
            }
            
            // Only prevent default if we're handling this event
            if (ourTouchEnded && e.preventDefault) e.preventDefault();
        }, { passive: false });
        
        jumpButton.addEventListener('touchcancel', (e) => {
            // Check if our specific touch was cancelled
            let ourTouchCancelled = false;
            for (let i = 0; i < e.changedTouches.length; i++) {
                if (e.changedTouches[i].identifier === this.jumpTouchId) {
                    ourTouchCancelled = true;
                    break;
                }
            }
            
            if (ourTouchCancelled) {
                this.jumpTouchId = null;
                this.touchControls['jump'] = false;
                jumpButton.classList.remove('active');
                console.log('Jump button touch cancelled');
            }
        }, { passive: false });
        
        // Pointer events as fallback for jump button
        jumpButton.addEventListener('pointerdown', (e) => {
            console.log('Jump button pointer down:', e.type);
            this.touchControls['jump'] = true;
            jumpButton.classList.add('active');
            this.resumeAudio();
            
            if (e.preventDefault) e.preventDefault();
            return false;
        });
        
        jumpButton.addEventListener('pointerup', (e) => {
            this.touchControls['jump'] = false;
            jumpButton.classList.remove('active');
            
            if (e.preventDefault) e.preventDefault();
            return false;
        });
        
        jumpButton.addEventListener('pointercancel', (e) => {
            this.touchControls['jump'] = false;
            jumpButton.classList.remove('active');
        });
        
        // Mouse events for desktop testing
        jumpButton.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this.touchControls['jump'] = true;
            jumpButton.classList.add('active');
            this.resumeAudio();
        });
        
        jumpButton.addEventListener('mouseup', (e) => {
            e.preventDefault();
            this.touchControls['jump'] = false;
            jumpButton.classList.remove('active');
        });
        
        // Prevent context menu on long press
        document.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    
    setupThumbstick() {
        const thumbstick = document.getElementById('thumbstick');
        const container = thumbstick.parentElement;
        
        // Get center position of thumbstick
        const updateCenter = () => {
            const rect = container.getBoundingClientRect();
            this.thumbstick.centerX = rect.left + rect.width / 2;
            this.thumbstick.centerY = rect.top + rect.height / 2;
        };
        
        updateCenter();
        window.addEventListener('resize', updateCenter);
        
        // Improved touch events with better multitouch support
        const handleStart = (e) => {
            // Only handle if thumbstick isn't already active
            if (this.thumbstick.active) return;
            
            console.log('Thumbstick touch start:', e.type, e.touches?.length || 'mouse');
            this.thumbstick.active = true;
            this.thumbstick.touchId = e.touches ? e.touches[0].identifier : 'mouse';
            thumbstick.classList.add('active');
            updateCenter();
            
            const touch = e.touches ? e.touches[0] : e;
            this.updateThumbstick(touch.clientX, touch.clientY);
            this.resumeAudio();
            
            // Prevent scrolling and other default behaviors
            if (e.preventDefault) e.preventDefault();
            return false;
        };
        
        const handleMove = (e) => {
            if (!this.thumbstick.active) return;
            
            // Find the correct touch by identifier
            let touch = null;
            if (e.touches && this.thumbstick.touchId !== 'mouse') {
                for (let i = 0; i < e.touches.length; i++) {
                    if (e.touches[i].identifier === this.thumbstick.touchId) {
                        touch = e.touches[i];
                        break;
                    }
                }
                if (!touch) return; // Our touch is not in the current touches
            } else if (!e.touches) {
                touch = e; // Mouse event
            }
            
            if (touch) {
                this.updateThumbstick(touch.clientX, touch.clientY);
            }
            
            // Prevent scrolling and other default behaviors
            if (e.preventDefault) e.preventDefault();
            return false;
        };
        
        const handleEnd = (e) => {
            if (!this.thumbstick.active) return;
            
            // Check if our specific touch ended
            let ourTouchEnded = false;
            if (e.changedTouches && this.thumbstick.touchId !== 'mouse') {
                for (let i = 0; i < e.changedTouches.length; i++) {
                    if (e.changedTouches[i].identifier === this.thumbstick.touchId) {
                        ourTouchEnded = true;
                        break;
                    }
                }
            } else if (!e.changedTouches) {
                ourTouchEnded = true; // Mouse event
            }
            
            if (ourTouchEnded) {
                console.log('Thumbstick touch end - our touch ended');
                this.thumbstick.active = false;
                this.thumbstick.touchId = null;
                thumbstick.classList.remove('active');
                
                // Reset to center
                this.thumbstick.moveX = 0;
                this.thumbstick.moveY = 0;
                thumbstick.style.transform = 'translate(-50%, -50%)';
            }
            
            // Only prevent default if we're handling this event
            if (ourTouchEnded && e.preventDefault) e.preventDefault();
        };
        
        // Touch events - only add move/end listeners when thumbstick is active
        thumbstick.addEventListener('touchstart', (e) => {
            handleStart(e);
            
            // Add document listeners only when thumbstick becomes active
            if (this.thumbstick.active) {
                document.addEventListener('touchmove', this.thumbstickMoveHandler, { passive: false });
                document.addEventListener('touchend', this.thumbstickEndHandler, { passive: false });
                document.addEventListener('touchcancel', this.thumbstickEndHandler, { passive: false });
            }
        }, { passive: false });
        
        // Store handlers so we can remove them
        this.thumbstickMoveHandler = handleMove;
        this.thumbstickEndHandler = (e) => {
            handleEnd(e);
            
            // Remove document listeners when thumbstick becomes inactive
            if (!this.thumbstick.active) {
                document.removeEventListener('touchmove', this.thumbstickMoveHandler);
                document.removeEventListener('touchend', this.thumbstickEndHandler);
                document.removeEventListener('touchcancel', this.thumbstickEndHandler);
            }
        };
        
        // Pointer events as fallback (often more reliable on some devices)
        thumbstick.addEventListener('pointerdown', (e) => {
            handleStart(e);
            
            if (this.thumbstick.active) {
                document.addEventListener('pointermove', this.thumbstickPointerMoveHandler);
                document.addEventListener('pointerup', this.thumbstickPointerEndHandler);
                document.addEventListener('pointercancel', this.thumbstickPointerEndHandler);
            }
        });
        
        // Store pointer handlers
        this.thumbstickPointerMoveHandler = handleMove;
        this.thumbstickPointerEndHandler = (e) => {
            handleEnd(e);
            
            if (!this.thumbstick.active) {
                document.removeEventListener('pointermove', this.thumbstickPointerMoveHandler);
                document.removeEventListener('pointerup', this.thumbstickPointerEndHandler);
                document.removeEventListener('pointercancel', this.thumbstickPointerEndHandler);
            }
        };
        
        // Mouse events for desktop testing
        thumbstick.addEventListener('mousedown', (e) => {
            handleStart(e);
            
            if (this.thumbstick.active) {
                document.addEventListener('mousemove', this.thumbstickMouseMoveHandler);
                document.addEventListener('mouseup', this.thumbstickMouseEndHandler);
            }
        });
        
        // Store mouse handlers
        this.thumbstickMouseMoveHandler = handleMove;
        this.thumbstickMouseEndHandler = (e) => {
            handleEnd(e);
            
            if (!this.thumbstick.active) {
                document.removeEventListener('mousemove', this.thumbstickMouseMoveHandler);
                document.removeEventListener('mouseup', this.thumbstickMouseEndHandler);
            }
        };
    }
    
    updateThumbstick(clientX, clientY) {
        const deltaX = clientX - this.thumbstick.centerX;
        const deltaY = clientY - this.thumbstick.centerY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        if (distance <= this.thumbstick.maxDistance) {
            this.thumbstick.currentX = deltaX;
            this.thumbstick.currentY = deltaY;
        } else {
            // Clamp to max distance
            const angle = Math.atan2(deltaY, deltaX);
            this.thumbstick.currentX = Math.cos(angle) * this.thumbstick.maxDistance;
            this.thumbstick.currentY = Math.sin(angle) * this.thumbstick.maxDistance;
        }
        
        // Calculate normalized movement (-1 to 1)
        this.thumbstick.moveX = this.thumbstick.currentX / this.thumbstick.maxDistance;
        this.thumbstick.moveY = this.thumbstick.currentY / this.thumbstick.maxDistance;
        
        // Update visual position
        const thumbstick = document.getElementById('thumbstick');
        thumbstick.style.transform = `translate(calc(-50% + ${this.thumbstick.currentX}px), calc(-50% + ${this.thumbstick.currentY}px))`;
    }
    
    resumeAudio() {
        if (this.audioContext && this.audioContext.state === 'suspended') {
            this.audioContext.resume().then(() => {
                console.log('Audio context resumed');
            });
        }
    }
    
    isKeyPressed(key) {
        // Check keyboard and touch controls
        switch(key) {
            case 'jump': return this.keys['Space'] || this.keys['ShiftLeft'] || this.keys['ShiftRight'] || this.touchControls['jump'];
            case 'restart': return this.keys['KeyR'];
            default: return false;
        }
    }
    
    getMovementInput() {
        // Combine keyboard and thumbstick input
        let moveX = 0, moveY = 0;
        
        // Keyboard input
        if (this.keys['KeyW'] || this.keys['ArrowUp']) moveY -= 1;
        if (this.keys['KeyS'] || this.keys['ArrowDown']) moveY += 1;
        if (this.keys['KeyA'] || this.keys['ArrowLeft']) moveX -= 1;
        if (this.keys['KeyD'] || this.keys['ArrowRight']) moveX += 1;
        
        // Thumbstick input (override keyboard if active)
        if (this.thumbstick.active) {
            moveX = this.thumbstick.moveX;
            moveY = this.thumbstick.moveY;
        }
        
        return { x: moveX, y: moveY };
    }
    
    createPlayer() {
        const geometry = new THREE.BoxGeometry(0.5, 0.5, 0.5);
        const material = new THREE.MeshLambertMaterial({ color: 0xcc3333 });
        const player = new THREE.Mesh(geometry, material);
        
        player.position.set(0, 1, 0);
        player.castShadow = true;
        player.receiveShadow = true;
        
        // Enhanced player physics properties
        player.velocity = new THREE.Vector3(0, 0, 0);
        player.onGround = false;
        player.wasOnGround = false;
        
        // Improved timing controls
        player.jumpBufferTimer = 0;
        player.coyoteTimer = 0;
        player.jumpBufferTime = 0.15;  // Increased for better feel
        player.coyoteTime = 0.12;
        
        // Enhanced movement parameters
        player.acceleration = 0.006;
        player.maxSpeed = 0.1;
        player.friction = 0.88;
        player.size = 0.25;
        
        // Visual effects
        player.squash = 1.0;
        player.squashRecoverySpeed = 3.0;
        
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
        
        // Store previous ground state for coyote time
        player.wasOnGround = player.onGround;
        
        // Update timers
        if (player.coyoteTimer > 0) player.coyoteTimer -= deltaTime;
        if (player.jumpBufferTimer > 0) player.jumpBufferTimer -= deltaTime;
        
        // Apply gravity when not on ground
        if (!player.onGround) {
            vel.y -= this.gravity;
        }
        
        // Handle movement input with improved acceleration
        const moveDir = this.getMovementInput();
        
        if (moveDir.x !== 0 || moveDir.y !== 0) {
            // Normalize movement vector
            const length = Math.sqrt(moveDir.x * moveDir.x + moveDir.y * moveDir.y);
            const normalizedX = moveDir.x / length;
            const normalizedZ = moveDir.y / length;
            
            // Apply acceleration
            vel.x += normalizedX * player.acceleration;
            vel.z += normalizedZ * player.acceleration;
        }
        
        // Handle jumping with improved buffering
        if (this.isKeyPressed('jump')) {
            // Set jump buffer when jump is pressed
            if (player.jumpBufferTimer <= 0) {
                player.jumpBufferTimer = player.jumpBufferTime;
            }
        }
        
        // Execute jump if conditions are met
        if (player.jumpBufferTimer > 0 && (player.onGround || player.coyoteTimer > 0)) {
            vel.y = this.jumpVelocity;
            player.onGround = false;
            player.coyoteTimer = 0;
            player.jumpBufferTimer = 0;
            player.squash = 1.3; // Visual squash effect
            console.log('Jump executed!');
            this.playJumpSound();
        }
        
        // Apply friction
        vel.x *= player.friction;
        vel.z *= player.friction;
        
        // Limit horizontal speed
        const horizontalSpeed = Math.sqrt(vel.x * vel.x + vel.z * vel.z);
        if (horizontalSpeed > player.maxSpeed) {
            vel.x = (vel.x / horizontalSpeed) * player.maxSpeed;
            vel.z = (vel.z / horizontalSpeed) * player.maxSpeed;
        }
        
        // Update position
        player.position.add(vel);
        
        // Check collisions with improved detection
        this.checkCollisions(player, deltaTime);
        
        // Implement coyote time
        if (player.wasOnGround && !player.onGround) {
            player.coyoteTimer = player.coyoteTime;
        }
        
        // Update visual effects
        this.updatePlayerVisuals(player, deltaTime);
        
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
    
    checkCollisions(player, deltaTime) {
        player.onGround = false;
        const size = player.size;
        
        for (let platform of this.platforms) {
            const px = platform.x, py = platform.y, pz = platform.z;
            const pw = platform.width, ph = platform.height, pd = platform.depth;
            
            // Enhanced AABB collision detection
            const playerLeft = player.position.x - size;
            const playerRight = player.position.x + size;
            const playerBottom = player.position.y - size;
            const playerTop = player.position.y + size;
            const playerFront = player.position.z - size;
            const playerBack = player.position.z + size;
            
            const platformLeft = px - pw/2;
            const platformRight = px + pw/2;
            const platformBottom = py - ph/2;
            const platformTop = py + ph/2;
            const platformFront = pz - pd/2;
            const platformBack = pz + pd/2;
            
            // Check for collision
            const xOverlap = playerRight > platformLeft && playerLeft < platformRight;
            const zOverlap = playerBack > platformFront && playerFront < platformBack;
            const yOverlap = playerTop > platformBottom && playerBottom < platformTop;
            
            if (xOverlap && zOverlap) {
                // Vertical collision (landing on platform)
                if (player.velocity.y <= 0 && 
                    playerBottom <= platformTop && 
                    playerBottom >= platformTop - 0.3) {
                    
                    // Landing effect
                    if (!player.wasOnGround && player.velocity.y < -0.05) {
                        console.log('Landing detected!');
                        player.squash = 1.4; // More pronounced landing squash
                        // Could add particle effects here
                    }
                    
                    player.position.y = platformTop + size;
                    player.velocity.y = 0;
                    player.onGround = true;
                    player.coyoteTimer = 0;
                    break;
                }
                
                // Side collisions (basic wall blocking)
                if (yOverlap) {
                    if (player.velocity.x > 0 && playerRight > platformLeft && playerLeft < platformLeft) {
                        player.position.x = platformLeft - size;
                        player.velocity.x = 0;
                    } else if (player.velocity.x < 0 && playerLeft < platformRight && playerRight > platformRight) {
                        player.position.x = platformRight + size;
                        player.velocity.x = 0;
                    }
                    
                    if (player.velocity.z > 0 && playerBack > platformFront && playerFront < platformFront) {
                        player.position.z = platformFront - size;
                        player.velocity.z = 0;
                    } else if (player.velocity.z < 0 && playerFront < platformBack && playerBack > platformBack) {
                        player.position.z = platformBack + size;
                        player.velocity.z = 0;
                    }
                }
            }
        }
    }
    
    updatePlayerVisuals(player, deltaTime) {
        // Handle squash effect recovery
        if (player.squash > 1.0) {
            player.squash -= deltaTime * player.squashRecoverySpeed;
            if (player.squash < 1.0) {
                player.squash = 1.0;
            }
        }
        
        // Apply squash to visual representation
        const scale = 1.0 / player.squash;
        const scaleXZ = player.squash;
        player.scale.set(scaleXZ, scale, scaleXZ);
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