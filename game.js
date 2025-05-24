// 3D Platformer Game in Three.js
class Game {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.scene = new THREE.Scene();
        
        // Adjust camera settings for better mobile experience
        const isMobile = window.innerWidth <= 768 || 'ontouchstart' in window;
        const fov = isMobile ? 60 : 45; // Wider FOV for mobile
        this.camera = new THREE.PerspectiveCamera(fov, window.innerWidth / window.innerHeight, 0.1, 50);
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true });
        
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio); // Important for mobile
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
        this.jumpPressed = false; // Track jump state for proper touch handling
        
        // Invisible touch zone system
        this.touchZones = {
            movement: {
                active: false,
                touchId: null,
                startX: 0,
                startY: 0,
                currentX: 0,
                currentY: 0,
                moveX: 0,
                moveY: 0,
                maxDistance: 80, // Maximum distance from start point
                sensitivity: 0.3, // INCREASED sensitivity for better control
                deadZone: 0.2, // REDUCED dead zone to prevent accidental movement
                smoothing: 0.8 // REDUCED smoothing factor for more responsive movement
            },
            jump: {
                active: false,
                touchId: null,
                justPressed: false // Track if jump was just pressed this frame
            }
        };
        
        // Game objects
        this.player = null;
        this.platforms = [];
        this.coins = [];
        this.particles = [];
        
        // Physics
        this.gravity = 0.008;
        this.jumpVelocity = 0.22;
        
        // Camera - Increased distances for better mobile view
        this.cameraTarget = new THREE.Vector3();
        this.cameraPosition = new THREE.Vector3(0, 5, 10); // Increased from (0, 3, 6)
        
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
        
        // Gamepad system
        this.gamepad = null;
        this.gamepadSupported = false;
        this.gamepadIndex = -1;
        this.gamepadConnected = false;
        
        // Camera rotation (for gamepad right stick control)
        this.cameraYaw = 0.0;      // Horizontal rotation
        this.cameraPitch = -20.0;  // Vertical rotation - start looking slightly down
        this.cameraDistance = 8.0; // Distance from player
        this.cameraSensitivity = 100.0; // Degrees per second
        this.cameraMode = 'follow'; // 'follow', 'gyro', or 'gamepad'
        
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
    
    setupGamepad() {
        // Check if Gamepad API is supported
        if (typeof navigator.getGamepads === 'function') {
            this.gamepadSupported = true;
            
            // Add gamepad event listeners
            window.addEventListener('gamepadconnected', (e) => {
                console.log(`🎮 Gamepad connected: ${e.gamepad.id}`);
                this.gamepad = e.gamepad;
                this.gamepadIndex = e.gamepad.index;
                this.gamepadConnected = true;
                
                // Check for 8bitdo controller
                if (e.gamepad.id.toLowerCase().includes('8bitdo') || 
                    e.gamepad.id.toLowerCase().includes('ultimate')) {
                    console.log('✓ 8bitdo Ultimate controller detected! Full feature support enabled.');
                }
                
                this.updateGamepadUI();
            });
            
            window.addEventListener('gamepaddisconnected', (e) => {
                console.log('🎮 Gamepad disconnected');
                this.gamepad = null;
                this.gamepadIndex = -1;
                this.gamepadConnected = false;
                this.cameraMode = 'follow'; // Revert to follow mode
                this.updateGamepadUI();
            });
            
            // Check for already connected gamepads
            this.scanForGamepads();
            
            console.log('Gamepad support initialized');
        } else {
            console.log('Gamepad API not supported in this browser');
        }
    }
    
    scanForGamepads() {
        const gamepads = navigator.getGamepads();
        for (let i = 0; i < gamepads.length; i++) {
            if (gamepads[i]) {
                console.log(`🎮 Found connected gamepad: ${gamepads[i].id}`);
                this.gamepad = gamepads[i];
                this.gamepadIndex = i;
                this.gamepadConnected = true;
                this.updateGamepadUI();
                break;
            }
        }
    }
    
    updateGamepadUI() {
        const gamepadStatus = document.getElementById('gamepad-status');
        if (gamepadStatus) {
            if (this.gamepadConnected && this.gamepad) {
                gamepadStatus.textContent = `🎮 ${this.gamepad.id.substring(0, 20)}...`;
                gamepadStatus.style.display = 'block';
            } else {
                gamepadStatus.style.display = 'none';
            }
        }
    }
    
    getGamepadInput() {
        if (!this.gamepadConnected || !this.gamepadSupported) return null;
        
        // Get fresh gamepad state (required by API)
        const gamepads = navigator.getGamepads();
        if (!gamepads[this.gamepadIndex]) return null;
        
        this.gamepad = gamepads[this.gamepadIndex];
        
        return {
            // Left stick (movement)
            leftStick: {
                x: this.gamepad.axes[0] || 0,
                y: this.gamepad.axes[1] || 0
            },
            // Right stick (camera)
            rightStick: {
                x: this.gamepad.axes[2] || 0,
                y: this.gamepad.axes[3] || 0
            },
            // Buttons
            buttons: {
                a: this.gamepad.buttons[0] && this.gamepad.buttons[0].pressed,      // A
                b: this.gamepad.buttons[1] && this.gamepad.buttons[1].pressed,      // B
                x: this.gamepad.buttons[2] && this.gamepad.buttons[2].pressed,      // X
                y: this.gamepad.buttons[3] && this.gamepad.buttons[3].pressed,      // Y
                lb: this.gamepad.buttons[4] && this.gamepad.buttons[4].pressed,     // L1/LB
                rb: this.gamepad.buttons[5] && this.gamepad.buttons[5].pressed,     // R1/RB
                back: this.gamepad.buttons[8] && this.gamepad.buttons[8].pressed,   // Back/Select
                start: this.gamepad.buttons[9] && this.gamepad.buttons[9].pressed,  // Start
            },
            // D-pad
            dpad: {
                up: this.gamepad.buttons[12] && this.gamepad.buttons[12].pressed,
                down: this.gamepad.buttons[13] && this.gamepad.buttons[13].pressed,
                left: this.gamepad.buttons[14] && this.gamepad.buttons[14].pressed,
                right: this.gamepad.buttons[15] && this.gamepad.buttons[15].pressed,
            }
        };
    }
    
    init() {
        this.setupLighting();
        this.setupControls();
        this.setupGyroscope(); // RE-ENABLED - works great on mobile!
        this.setupGamepad();   // NEW - gamepad support
        this.loadLevel(1);
        this.updateUI();
        this.animate();
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        console.log('3D Platformer Game Started!');
        console.log('Controls: WASD/Arrows - Move, Space/Shift - Jump');
        console.log('Mobile: Left half - Move, Right half - Jump');
        console.log('Gamepad: Left stick - Move, Right stick - Camera, Face buttons - Jump');
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
            // Prevent certain keys from triggering file input accidentally
            if (event.code === 'KeyL' && (event.ctrlKey || event.metaKey)) {
                event.preventDefault(); // Prevent Ctrl+L from opening file dialog
                return;
            }
            
            // Camera reset
            if (event.code === 'KeyV') {
                this.resetCamera();
                console.log('Camera reset to default position');
            }
            
            this.keys[event.code] = true;
            this.resumeAudio(); // Enable audio on first interaction
        });
        
        document.addEventListener('keyup', (event) => {
            this.keys[event.code] = false;
        });
        
        // Invisible touch zone system
        this.setupInvisibleTouchZones();
        
        // Prevent context menu on long press
        document.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    
    setupInvisibleTouchZones() {
        const canvas = document.getElementById('gameCanvas');
        
        // Touch event handlers for the invisible zones
        const handleTouchStart = (e) => {
            this.resumeAudio();
            
            for (let i = 0; i < e.changedTouches.length; i++) {
                const touch = e.changedTouches[i];
                const x = touch.clientX;
                const y = touch.clientY;
                
                // Use actual viewport dimensions
                const viewportWidth = window.innerWidth;
                const viewportHeight = window.innerHeight;
                
                console.log(`Touch start at: ${x}, ${y} (viewport: ${viewportWidth}x${viewportHeight})`);
                
                // Determine which zone was touched
                if (x < viewportWidth / 2) {
                    // Left half - movement control
                    if (!this.touchZones.movement.active) {
                        this.touchZones.movement.active = true;
                        this.touchZones.movement.touchId = touch.identifier;
                        this.touchZones.movement.startX = x;
                        this.touchZones.movement.startY = y;
                        this.touchZones.movement.currentX = 0;
                        this.touchZones.movement.currentY = 0;
                        this.touchZones.movement.moveX = 0;
                        this.touchZones.movement.moveY = 0;
                        console.log('Movement zone activated');
                        this.updateTouchDebug();
                    }
                } else {
                    // Right half - jump control
                    if (!this.touchZones.jump.active) {
                        this.touchZones.jump.active = true;
                        this.touchZones.jump.touchId = touch.identifier;
                        this.touchZones.jump.justPressed = true; // Mark as just pressed
                        console.log('Jump zone activated - jump triggered!');
                        this.updateTouchDebug();
                    }
                }
            }
            
            e.preventDefault();
        };
        
        const handleTouchMove = (e) => {
            for (let i = 0; i < e.touches.length; i++) {
                const touch = e.touches[i];
                
                // Check if this is our movement touch
                if (this.touchZones.movement.active && 
                    touch.identifier === this.touchZones.movement.touchId) {
                    
                    const deltaX = touch.clientX - this.touchZones.movement.startX;
                    const deltaY = touch.clientY - this.touchZones.movement.startY;
                    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                    
                    if (distance <= this.touchZones.movement.maxDistance) {
                        this.touchZones.movement.currentX = deltaX;
                        this.touchZones.movement.currentY = deltaY;
                    } else {
                        // Clamp to max distance
                        const angle = Math.atan2(deltaY, deltaX);
                        this.touchZones.movement.currentX = Math.cos(angle) * this.touchZones.movement.maxDistance;
                        this.touchZones.movement.currentY = Math.sin(angle) * this.touchZones.movement.maxDistance;
                    }
                    
                    // Calculate normalized movement (-1 to 1) with sensitivity and dead zone
                    let rawMoveX = this.touchZones.movement.currentX / this.touchZones.movement.maxDistance;
                    let rawMoveY = this.touchZones.movement.currentY / this.touchZones.movement.maxDistance;
                    
                    // Apply dead zone
                    const rawDistance = Math.sqrt(rawMoveX * rawMoveX + rawMoveY * rawMoveY);
                    if (rawDistance < this.touchZones.movement.deadZone) {
                        rawMoveX = 0;
                        rawMoveY = 0;
                    } else {
                        // Scale to account for dead zone
                        const scale = (rawDistance - this.touchZones.movement.deadZone) / (1 - this.touchZones.movement.deadZone);
                        const angle = Math.atan2(rawMoveY, rawMoveX);
                        rawMoveX = Math.cos(angle) * scale;
                        rawMoveY = Math.sin(angle) * scale;
                    }
                    
                    // Apply sensitivity scaling - DIRECTLY apply the values
                    this.touchZones.movement.moveX = rawMoveX * this.touchZones.movement.sensitivity;
                    this.touchZones.movement.moveY = rawMoveY * this.touchZones.movement.sensitivity;
                    
                    // Debug output for mobile
                    if (rawDistance > 0.1) {
                        console.log(`Touch: raw(${rawMoveX.toFixed(2)}, ${rawMoveY.toFixed(2)}) final(${this.touchZones.movement.moveX.toFixed(2)}, ${this.touchZones.movement.moveY.toFixed(2)})`);
                    }
                    
                    this.updateTouchDebug();
                    break;
                }
            }
            
            e.preventDefault();
        };
        
        const handleTouchEnd = (e) => {
            for (let i = 0; i < e.changedTouches.length; i++) {
                const touch = e.changedTouches[i];
                
                // Check if movement touch ended
                if (this.touchZones.movement.active && 
                    touch.identifier === this.touchZones.movement.touchId) {
                    
                    this.touchZones.movement.active = false;
                    this.touchZones.movement.touchId = null;
                    // Don't immediately zero - let it decay naturally through smoothing
                    this.touchZones.movement.currentX = 0;
                    this.touchZones.movement.currentY = 0;
                    console.log('Movement zone deactivated');
                    this.updateTouchDebug();
                }
                
                // Check if jump touch ended
                if (this.touchZones.jump.active && 
                    touch.identifier === this.touchZones.jump.touchId) {
                    
                    this.touchZones.jump.active = false;
                    this.touchZones.jump.touchId = null;
                    this.touchZones.jump.justPressed = false; // Clear just pressed flag
                    console.log('Jump zone deactivated');
                    this.updateTouchDebug();
                }
            }
            
            e.preventDefault();
        };
        
        // Add touch event listeners to the canvas
        canvas.addEventListener('touchstart', handleTouchStart, { passive: false });
        canvas.addEventListener('touchmove', handleTouchMove, { passive: false });
        canvas.addEventListener('touchend', handleTouchEnd, { passive: false });
        canvas.addEventListener('touchcancel', handleTouchEnd, { passive: false });
        
        console.log('Invisible touch zones setup complete - left half: movement, right half: jump');
    }
    
    resumeAudio() {
        if (this.audioContext && this.audioContext.state === 'suspended') {
            this.audioContext.resume().then(() => {
                console.log('Audio context resumed');
            });
        }
    }
    
    isKeyPressed(key) {
        // Check keyboard, touch controls, and gamepad
        switch(key) {
            case 'jump': 
                // Check if jump was just pressed (keyboard, touch, or gamepad)
                const keyboardJump = this.keys['Space'] || this.keys['ShiftLeft'] || this.keys['ShiftRight'];
                const touchJump = this.touchZones.jump.justPressed;
                
                // Gamepad face buttons (A, B, X, Y)
                let gamepadJump = false;
                const gamepadInput = this.getGamepadInput();
                if (gamepadInput) {
                    gamepadJump = gamepadInput.buttons.a || gamepadInput.buttons.b || 
                                 gamepadInput.buttons.x || gamepadInput.buttons.y;
                }
                
                // Track overall jump state for edge detection
                const currentJumpState = keyboardJump || this.touchZones.jump.active || gamepadJump;
                const jumpJustPressed = (currentJumpState && !this.jumpPressed) || touchJump;
                
                return jumpJustPressed;
            case 'restart': 
                const keyboardRestart = this.keys['KeyR'];
                let gamepadRestart = false;
                const gamepadInput2 = this.getGamepadInput();
                if (gamepadInput2) {
                    gamepadRestart = gamepadInput2.buttons.back; // Back/Select button
                }
                return keyboardRestart || gamepadRestart;
            default: return false;
        }
    }
    
    getMovementInput() {
        // Combine keyboard, touch zones, and gamepad input
        let moveX = 0, moveY = 0;
        
        // Keyboard input
        if (this.keys['KeyW'] || this.keys['ArrowUp']) moveY -= 1;
        if (this.keys['KeyS'] || this.keys['ArrowDown']) moveY += 1;
        if (this.keys['KeyA'] || this.keys['ArrowLeft']) moveX -= 1;
        if (this.keys['KeyD'] || this.keys['ArrowRight']) moveX += 1;
        
        // Gamepad input (left stick and D-pad)
        const gamepadInput = this.getGamepadInput();
        if (gamepadInput) {
            const deadzone = 0.15;
            
            // Left stick input
            if (Math.abs(gamepadInput.leftStick.x) > deadzone) {
                moveX += gamepadInput.leftStick.x;
            }
            if (Math.abs(gamepadInput.leftStick.y) > deadzone) {
                moveY += gamepadInput.leftStick.y;
            }
            
            // D-pad input
            if (gamepadInput.dpad.left) moveX -= 1;
            if (gamepadInput.dpad.right) moveX += 1;
            if (gamepadInput.dpad.up) moveY -= 1;
            if (gamepadInput.dpad.down) moveY += 1;
        }
        
        // Touch zones input (override keyboard and gamepad if active)
        if (this.touchZones.movement.active) {
            moveX = this.touchZones.movement.moveX;
            moveY = this.touchZones.movement.moveY;
        } else {
            // Apply decay when not actively touching - SIMPLIFIED
            if (Math.abs(this.touchZones.movement.moveX) > 0.01 || Math.abs(this.touchZones.movement.moveY) > 0.01) {
                this.touchZones.movement.moveX *= 0.5; // Faster decay
                this.touchZones.movement.moveY *= 0.5;
                moveX = this.touchZones.movement.moveX;
                moveY = this.touchZones.movement.moveY;
                this.updateTouchDebug();
            } else {
                // Stop completely when very small
                this.touchZones.movement.moveX = 0;
                this.touchZones.movement.moveY = 0;
            }
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
    
    createPlatform(x, y, z, width, height, depth, color = 0x22aa22, friction = 0.88) {
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
        
        // Ensure coin is positioned above any platforms at this location
        let safeY = y;
        for (let platform of this.platforms) {
            const px = platform.x, py = platform.y, pz = platform.z;
            const pw = platform.width, ph = platform.height, pd = platform.depth;
            
            // Check if coin would be inside or too close to this platform
            if (Math.abs(x - px) < pw/2 + 0.2 && 
                Math.abs(z - pz) < pd/2 + 0.2 && 
                y >= py - ph/2 && y <= py + ph/2 + 0.5) {
                
                // Position coin safely above this platform
                safeY = Math.max(safeY, py + ph/2 + 0.4);
            }
        }
        
        coin.position.set(x, safeY, z);
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
                    [0, -0.5, 0, 4, 0.5, 4, 0x1a5c1a, 0.88],      // Base - normal friction
                    [0, -0.2, -2, 1.5, 0.3, 1.5, 0x22aa22, 0.88], // Normal platform
                    [2, 0.2, -2, 1, 0.3, 1, 0x22aa22, 0.88],      // Normal platform
                    [3, 0.6, 0, 1, 0.3, 1, 0x22aa22, 0.88],       // Normal platform
                    [2, 1.0, 2, 1, 0.3, 1, 0x22aa22, 0.88],       // Normal platform
                    [0, 1.4, 3, 1.5, 0.3, 1.5, 0x22aa22, 0.88],   // Normal platform
                    [-2, 1.8, 2, 1, 0.3, 1, 0x22aa22, 0.88],      // Normal platform
                ],
                coins: [
                    [0, 0.5, -2], [2, 0.9, -2], [3, 1.3, 0],
                    [2, 1.7, 2], [0, 2.1, 3], [-2, 2.5, 2]
                ]
            },
            2: {
                // Precision jumping with slippery platforms
                platforms: [
                    [0, -0.5, 0, 4, 0.5, 4, 0x1a5c1a, 0.88],      // Base - normal
                    [1, -0.2, -3, 1, 0.2, 1, 0x4444ff, 0.98],     // Slippery ice platform
                    [3, 0.1, -2, 1, 0.2, 1, 0x4444ff, 0.98],      // Slippery ice platform
                    [4, 0.5, 0, 1, 0.2, 1, 0x2222aa, 0.88],       // Normal platform
                    [3, 0.9, 2, 1, 0.2, 1, 0x4444ff, 0.98],       // Slippery ice platform
                    [1, 1.3, 3, 1, 0.2, 1, 0x2222aa, 0.88],       // Normal platform
                    [-1, 1.7, 3, 1, 0.2, 1, 0x4444ff, 0.98],      // Slippery ice platform
                    [-3, 2.1, 2, 1, 0.2, 1, 0x2222aa, 0.88],      // Normal platform
                    [-4, 2.5, 0, 1, 0.2, 1, 0x4444ff, 0.98],      // Slippery ice platform
                    [-3, 2.9, -2, 1, 0.2, 1, 0x2222aa, 0.88],     // Normal platform
                    [-1, 3.3, -3, 2, 0.2, 2, 0x2222aa, 0.88],     // Normal platform
                ],
                coins: [
                    [1, 0.5, -3], [3, 0.8, -2], [4, 1.2, 0], [3, 1.6, 2],
                    [1, 2.0, 3], [-1, 2.4, 3], [-3, 2.8, 2], [-4, 3.2, 0],
                    [-3, 3.6, -2], [-1, 4.0, -3]
                ]
            },
            3: {
                // Spiral tower with grippy platforms
                platforms: [
                    [0, -0.5, 0, 3, 0.5, 3, 0x1a5c1a, 0.88],      // Base - normal
                    [2, 0.0, 0, 1, 0.2, 1, 0xcc4444, 0.70],       // Grippy platform
                    [2, 0.4, -2, 1, 0.2, 1, 0xcc4444, 0.70],      // Grippy platform
                    [0, 0.8, -3, 1, 0.2, 1, 0xaa2222, 0.88],      // Normal platform
                    [-2, 1.2, -2, 1, 0.2, 1, 0xcc4444, 0.70],     // Grippy platform
                    [-3, 1.6, 0, 1, 0.2, 1, 0xaa2222, 0.88],      // Normal platform
                    [-2, 2.0, 2, 1, 0.2, 1, 0xcc4444, 0.70],      // Grippy platform
                    [0, 2.4, 3, 1, 0.2, 1, 0xaa2222, 0.88],       // Normal platform
                    [2, 2.8, 2, 1, 0.2, 1, 0xcc4444, 0.70],       // Grippy platform
                    [3, 3.2, 0, 1, 0.2, 1, 0xaa2222, 0.88],       // Normal platform
                    [2, 3.6, -1, 1, 0.2, 1, 0xcc4444, 0.70],      // Grippy platform
                    [0, 4.0, -2, 2, 0.2, 2, 0xaa2222, 0.88],      // Normal platform
                ],
                coins: [
                    [2, 0.7, 0], [2, 1.1, -2], [0, 1.5, -3], [-2, 1.9, -2],
                    [-3, 2.3, 0], [-2, 2.7, 2], [0, 3.1, 3], [2, 3.5, 2],
                    [3, 3.9, 0], [2, 4.3, -1], [0, 4.7, -2]
                ]
            },
            4: {
                // Long jumps and gaps with mixed friction
                platforms: [
                    [0, -0.5, 0, 2, 0.5, 2, 0x1a5c1a, 0.88],      // Base - normal
                    [4, 0.0, 0, 1.5, 0.3, 1.5, 0xaaaa22, 0.88],   // Normal platform
                    [8, 0.3, -1, 1, 0.3, 1, 0x4444ff, 0.98],      // Slippery ice platform
                    [6, 0.8, -4, 1, 0.3, 1, 0xcc4444, 0.70],      // Grippy platform
                    [2, 1.2, -5, 1, 0.3, 1, 0x4444ff, 0.98],      // Slippery ice platform
                    [-2, 1.6, -4, 1, 0.3, 1, 0xaaaa22, 0.88],     // Normal platform
                    [-5, 2.0, -1, 1, 0.3, 1, 0xcc4444, 0.70],     // Grippy platform
                    [-7, 2.4, 2, 1, 0.3, 1, 0x4444ff, 0.98],      // Slippery ice platform
                    [-4, 2.8, 5, 1, 0.3, 1, 0xaaaa22, 0.88],      // Normal platform
                    [0, 3.2, 6, 1, 0.3, 1, 0xcc4444, 0.70],       // Grippy platform
                    [4, 3.6, 4, 1, 0.3, 1, 0x4444ff, 0.98],       // Slippery ice platform
                    [7, 4.0, 1, 1.5, 0.3, 1.5, 0xaaaa22, 0.88],   // Normal platform
                ],
                coins: [
                    [4, 0.7, 0], [8, 1.0, -1], [6, 1.5, -4], [2, 1.9, -5],
                    [-2, 2.3, -4], [-5, 2.7, -1], [-7, 3.1, 2], [-4, 3.5, 5],
                    [0, 3.9, 6], [4, 4.3, 4], [7, 4.7, 1]
                ]
            },
            5: {
                // Moving maze with extreme friction variations
                platforms: [
                    [0, -0.5, 0, 2, 0.5, 2, 0x1a5c1a, 0.88],      // Base - normal
                    [3, 0.0, 0, 1, 0.2, 3, 0x6666ff, 0.99],       // Super slippery ice
                    [1, 0.4, 3, 3, 0.2, 1, 0xcc4444, 0.70],       // Grippy platform
                    [-1, 0.8, 5, 1, 0.2, 1, 0xaaaaaa, 0.88],      // Normal platform
                    [-4, 1.2, 4, 1, 0.2, 3, 0x6666ff, 0.99],      // Super slippery ice
                    [-6, 1.6, 1, 3, 0.2, 1, 0xcc4444, 0.70],      // Grippy platform
                    [-4, 2.0, -1, 1, 0.2, 1, 0xaaaaaa, 0.88],     // Normal platform
                    [-1, 2.4, -2, 1, 0.2, 3, 0x6666ff, 0.99],     // Super slippery ice
                    [2, 2.8, -1, 1, 0.2, 1, 0xcc4444, 0.70],      // Grippy platform
                    [5, 3.2, 0, 1, 0.2, 3, 0xaaaaaa, 0.88],       // Normal platform
                    [3, 3.6, 3, 3, 0.2, 1, 0x6666ff, 0.99],       // Super slippery ice
                    [0, 4.0, 5, 1, 0.2, 1, 0xcc4444, 0.70],       // Grippy platform
                    [-3, 4.4, 3, 1, 0.2, 1, 0xaaaaaa, 0.88],      // Normal platform
                    [-5, 4.8, 0, 1, 0.2, 1, 0x6666ff, 0.99],      // Super slippery ice
                    [-2, 5.2, -2, 3, 0.2, 1, 0xcc4444, 0.70],     // Grippy platform
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
        currentLevel.platforms.forEach(([x, y, z, w, h, d, color, friction]) => {
            const platform = this.createPlatform(x, y, z, w, h, d, color, friction);
            this.platforms.push({ 
                mesh: platform, 
                x, y, z, 
                width: w, height: h, depth: d,
                friction: friction || 0.88 // Default friction if not specified
            });
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
        
        // Track jump state for edge detection
        const keyboardJump = this.keys['Space'] || this.keys['ShiftLeft'] || this.keys['ShiftRight'];
        const currentJumpState = keyboardJump || this.touchZones.jump.active;
        
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
                console.log('Jump buffer set!');
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
        
        // Update jump state tracking and clear touch jump flag
        this.jumpPressed = currentJumpState;
        this.touchZones.jump.justPressed = false; // Clear each frame
        
        // Handle gamepad special buttons
        const gamepadInput = this.getGamepadInput();
        if (gamepadInput) {
            // Start button for pause (future implementation)
            if (gamepadInput.buttons.start) {
                console.log('Start button pressed - pause functionality could go here');
            }
            
            // Shoulder buttons for level switching (future implementation)
            if (gamepadInput.buttons.lb) {
                console.log('Left bumper pressed - previous level functionality could go here');
            }
            if (gamepadInput.buttons.rb) {
                console.log('Right bumper pressed - next level functionality could go here');
            }
        }
        
        // Apply friction - use platform-specific friction if on ground
        let currentFriction = player.friction; // Default player friction
        
        if (player.onGround) {
            // Find which platform the player is on and use its friction
            for (let platform of this.platforms) {
                const px = platform.x, py = platform.y, pz = platform.z;
                const pw = platform.width, ph = platform.height, pd = platform.depth;
                
                // Check if player is on this platform
                if (Math.abs(player.position.x - px) < pw/2 + player.size &&
                    Math.abs(player.position.z - pz) < pd/2 + player.size &&
                    Math.abs(player.position.y - (py + ph/2 + player.size)) < 0.1) {
                    
                    currentFriction = platform.friction;
                    break;
                }
            }
        }
        
        vel.x *= currentFriction;
        vel.z *= currentFriction;
        
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
        
        // Rotate coins and apply floating animation
        this.coins.forEach(coin => {
            coin.rotation.y = this.coinRotation;
            
            // Use the original Y position as base + floating offset
            if (!coin.originalY) {
                coin.originalY = coin.position.y; // Store original position on first update
            }
            
            // Apply floating animation from the original position
            const floatOffset = Math.sin(this.coinRotation * 0.5) * 0.1;
            coin.position.y = coin.originalY + floatOffset;
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
        // Handle gamepad camera input first (if connected)
        const gamepadInput = this.getGamepadInput();
        if (gamepadInput && this.gamepadConnected) {
            const deadzone = 0.1;
            const rightStick = gamepadInput.rightStick;
            
            // Apply right stick camera rotation
            if (Math.abs(rightStick.x) > deadzone || Math.abs(rightStick.y) > deadzone) {
                const deltaTime = 1/60; // Approximate for smooth camera
                
                if (Math.abs(rightStick.x) > deadzone) {
                    this.cameraYaw += rightStick.x * this.cameraSensitivity * deltaTime;
                }
                if (Math.abs(rightStick.y) > deadzone) {
                    this.cameraPitch += rightStick.y * this.cameraSensitivity * deltaTime;
                }
                
                // Clamp pitch to prevent camera flipping
                this.cameraPitch = Math.max(-80.0, Math.min(80.0, this.cameraPitch));
                
                // Switch to gamepad camera mode when using right stick
                this.cameraMode = 'gamepad';
            }
        }
        
        if (this.cameraMode === 'gamepad' && this.gamepadConnected) {
            // Gamepad-controlled camera (right stick)
            const yawRad = (this.cameraYaw * Math.PI) / 180;
            const pitchRad = (this.cameraPitch * Math.PI) / 180;
            
            // Calculate camera position using spherical coordinates
            const horizontalDistance = this.cameraDistance * Math.cos(pitchRad);
            
            const cameraOffsetX = horizontalDistance * Math.sin(yawRad);
            const cameraOffsetZ = horizontalDistance * Math.cos(yawRad);
            const cameraOffsetY = this.cameraDistance * Math.sin(pitchRad);
            
            // Position camera relative to player
            const targetX = this.player.position.x + cameraOffsetX;
            const targetY = this.player.position.y + cameraOffsetY + 2.0;
            const targetZ = this.player.position.z + cameraOffsetZ;
            
            // Smooth camera movement
            this.cameraPosition.set(targetX, targetY, targetZ);
            this.camera.position.lerp(this.cameraPosition, 0.15);
            this.camera.lookAt(this.player.position);
            
        } else if (this.gyroEnabled && this.gyroSupported) {
            // Gyroscope-controlled camera
            this.cameraMode = 'gyro';
            const sensitivity = 0.5;
            
            // Calculate relative rotation from base orientation
            const deltaAlpha = (this.deviceOrientation.alpha - this.baseOrientation.alpha) * Math.PI / 180;
            const deltaBeta = (this.deviceOrientation.beta - this.baseOrientation.beta) * Math.PI / 180;
            const deltaGamma = (this.deviceOrientation.gamma - this.baseOrientation.gamma) * Math.PI / 180;
            
            // Calculate camera position using spherical coordinates around player
            const distance = 12; // Increased from 8
            const height = 5; // Increased from 3
            
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
            // Standard smooth camera follow - Increased distances for better mobile view
            this.cameraMode = 'follow';
            this.cameraTarget.set(
                this.player.position.x + 6, // Increased from 4
                this.player.position.y + 5, // Increased from 3
                this.player.position.z + 8  // Increased from 5
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
        // Adjust FOV based on mobile detection
        const isMobile = window.innerWidth <= 768 || 'ontouchstart' in window;
        const fov = isMobile ? 60 : 45;
        this.camera.fov = fov;
        
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        
        // Log resize for debugging mobile issues
        console.log(`Viewport resized: ${window.innerWidth}x${window.innerHeight}, DPR: ${window.devicePixelRatio}, FOV: ${fov}`);
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
    
    updateTouchDebug() {
        const debugElement = document.getElementById('touch-debug');
        if (debugElement) {
            let status = '';
            
            // Show input method priority
            if (this.gamepadConnected) {
                status += '🎮 Gamepad | ';
            }
            if (this.touchZones.movement.active || this.touchZones.jump.active) {
                status += '👆 Touch | ';
            }
            status += '⌨️ Keyboard';
            
            // Show camera mode
            status += ` | Cam: ${this.cameraMode}`;
            
            // Touch zones status
            if (this.touchZones.movement.active) {
                const x = this.touchZones.movement.moveX.toFixed(2);
                const y = this.touchZones.movement.moveY.toFixed(2);
                status += ` | Move(${x},${y})`;
            }
            
            if (this.touchZones.jump.active) {
                status += ' | Jump(ON)';
            }
            
            debugElement.textContent = status;
        }
    }
    
    loadCustomLevel(levelData) {
        console.log('Loading custom level...', levelData);
        
        // Clear existing level
        this.platforms.forEach(platform => this.scene.remove(platform.mesh));
        this.coins.forEach(coin => this.scene.remove(coin));
        
        this.platforms = [];
        this.coins = [];
        
        // Reset player
        this.resetPlayer();
        
        try {
            // Load platforms
            const platforms = levelData.platforms || [];
            const platformColors = levelData.platform_colors || [];
            
            platforms.forEach((platformData, index) => {
                const [x, y, z, width, height, depth] = platformData;
                
                // Convert color from editor format (0-1 range) to Three.js format (hex)
                let color = 0x22aa22; // Default green
                if (index < platformColors.length) {
                    const [r, g, b] = platformColors[index];
                    color = (Math.floor(r * 255) << 16) | (Math.floor(g * 255) << 8) | Math.floor(b * 255);
                }
                
                // Create platform with default friction
                const platform = this.createPlatform(x, y, z, width, height, depth, color, 0.88);
                this.platforms.push({ 
                    mesh: platform, 
                    x, y, z, 
                    width, height, depth,
                    friction: 0.88
                });
            });
            
            // Load coins
            const coins = levelData.coins || [];
            coins.forEach(([x, y, z]) => {
                const coin = this.createCoin(x, y, z);
                this.coins.push(coin);
            });
            
            // Update level indicator to show custom
            this.level = 'Custom';
            this.updateUI();
            
            console.log(`✓ Custom level loaded: ${this.platforms.length} platforms, ${this.coins.length} coins`);
            
        } catch (error) {
            console.error('Error processing custom level data:', error);
            throw error;
        }
    }
    
    resetCamera() {
        this.cameraYaw = 0.0;
        this.cameraPitch = -20.0;
        this.cameraMode = 'follow';
        
        // Reset camera position to default follow mode
        this.cameraTarget.set(
            this.player.position.x + 6,
            this.player.position.y + 5,
            this.player.position.z + 8
        );
        this.cameraPosition.copy(this.cameraTarget);
        this.camera.position.copy(this.cameraPosition);
        this.camera.lookAt(this.player.position);
    }
}

// Start the game when page loads
window.addEventListener('load', () => {
    window.game = new Game(); // Store globally for custom level loading
}); 