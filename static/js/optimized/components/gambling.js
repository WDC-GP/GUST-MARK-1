/**
 * GUST Bot Enhanced - Gambling Games Component
 * ============================================
 * Modular component for gambling games including slots,coinflip,and dice
 */
class GamblingComponent extends BaseComponent{constructor(containerId,options ={}){super(containerId,options);this.api = options.api || window.App.api;this.eventBus = options.eventBus || window.App.eventBus;this.stateManager = options.stateManager || window.App.stateManager;}get defaultOptions(){return{...super.defaultOptions,enableSlots: true,enableCoinflip: true,enableDice: true,maxBetAmount: 10000,minBetAmount: 1,showHistory: true,animationDuration: 2000};}getInitialState(){return{...super.getInitialState(),slotsUserId: '',slotsBet: 0,slotsResult: null,slotsSpinning: false,coinflipUserId: '',coinflipBet: 0,coinflipChoice: 'heads',coinflipResult: null,coinflipFlipping: false,diceUserId: '',diceBet: 0,dicePrediction: 1,diceResult: null,diceRolling: false,history: [],stats:{},leaderboard: []};}render(){this.container.innerHTML = `
 <div class="gambling-games">
 <div class="gambling-header">
 <h2 class="text-3xl font-bold mb-6">🎰 Gambling Games</h2>
 <div class="gambling-warning bg-yellow-800 border border-yellow-600 p-4 rounded-lg mb-6">
 <p class="text-yellow-200">
 <strong>⚠️ Warning:</strong> Gambling can be addictive. Play responsibly with in-game currency only.
 </p>
 </div>
 </div>
 <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
 ${this.options.enableSlots ? this.renderSlotsGame() : ''}${this.options.enableCoinflip ? this.renderCoinflipGame() : ''}${this.options.enableDice ? this.renderDiceGame() : ''}</div>
 ${this.options.showHistory ? this.renderHistorySection() : ''}<div class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
 <!-- Gambling Stats -->
 <div class="bg-gray-800 p-6 rounded-lg">
 <h3 class="text-xl font-semibold mb-4">📊 Gambling Statistics</h3>
 <div id="gamblingStats">
 <!-- Stats will be populated here -->
 </div>
 </div>
 <!-- Leaderboard -->
 <div class="bg-gray-800 p-6 rounded-lg">
 <h3 class="text-xl font-semibold mb-4">🏆 High Rollers</h3>
 <div id="gamblingLeaderboard">
 <!-- Leaderboard will be populated here -->
 </div>
 </div>
 </div>
 </div>
 `;}renderSlotsGame(){return `
 <div class="bg-gray-800 p-6 rounded-lg">
 <h3 class="text-xl font-semibold mb-4">🎰 Slot Machine</h3>
 <div class="space-y-4">
 <!-- Slot Display -->
 <div class="slots-display bg-gray-900 p-6 rounded-lg border-4 border-yellow-600">
 <div id="slotsReels" class="flex justify-center items-center space-x-4 text-6xl mb-4">
 <div class="reel">🍒</div>
 <div class="reel">🍒</div>
 <div class="reel">🍒</div>
 </div>
 <div class="text-center">
 <div class="text-sm text-gray-400 mb-2">Paytable</div>
 <div class="text-xs text-gray-300 space-y-1">
 <div>💎💎💎 = 10x bet</div>
 <div>⭐⭐⭐ = 5x bet</div>
 <div>🍒🍒🍒 / 🍋🍋🍋 / 🔔🔔🔔 = 3x bet</div>
 <div>Any 2 matching = 2x bet</div>
 </div>
 </div>
 </div>
 <!-- Controls -->
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">User ID</label>
 <input type="text" 
 id="slotsUserId" 
 placeholder="Enter User ID" 
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
 value="${this.state.slotsUserId}">
 </div>
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">Bet Amount</label>
 <input type="number" 
 id="slotsBet" 
 placeholder="Bet Amount" 
 min="${this.options.minBetAmount}"
 max="${this.options.maxBetAmount}"
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
 value="${this.state.slotsBet}">
 </div>
 <button id="spinSlotsBtn" 
 class="w-full bg-purple-600 hover:bg-purple-700 p-3 rounded font-medium">
 🎰 SPIN!
 </button>
 <div id="slotsResult" class="text-center min-h-[80px]">
 <!-- Results will appear here -->
 </div>
 </div>
 </div>
 `;}renderCoinflipGame(){return `
 <div class="bg-gray-800 p-6 rounded-lg">
 <h3 class="text-xl font-semibold mb-4">🪙 Coinflip</h3>
 <div class="space-y-4">
 <!-- Coin Display -->
 <div class="coin-display bg-gray-900 p-6 rounded-lg border-4 border-blue-600">
 <div id="coinAnimation" class="flex justify-center items-center text-8xl mb-4">
 🪙
 </div>
 <div class="text-center">
 <div class="text-sm text-gray-400">Choose Heads or Tails</div>
 <div class="text-sm text-gray-300">Win 2x your bet!</div>
 </div>
 </div>
 <!-- Controls -->
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">User ID</label>
 <input type="text" 
 id="coinflipUserId" 
 placeholder="Enter User ID" 
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
 value="${this.state.coinflipUserId}">
 </div>
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">Bet Amount</label>
 <input type="number" 
 id="coinflipBet" 
 placeholder="Bet Amount" 
 min="${this.options.minBetAmount}"
 max="${this.options.maxBetAmount}"
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
 value="${this.state.coinflipBet}">
 </div>
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">Your Choice</label>
 <select id="coinflipChoice" 
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
 <option value="heads" ${this.state.coinflipChoice === 'heads' ? 'selected' : ''}>🟡 Heads</option>
 <option value="tails" ${this.state.coinflipChoice === 'tails' ? 'selected' : ''}>⚪ Tails</option>
 </select>
 </div>
 <button id="flipCoinBtn" 
 class="w-full bg-green-600 hover:bg-green-700 p-3 rounded font-medium">
 🪙 FLIP!
 </button>
 <div id="coinflipResult" class="text-center min-h-[80px]">
 <!-- Results will appear here -->
 </div>
 </div>
 </div>
 `;}renderDiceGame(){return `
 <div class="bg-gray-800 p-6 rounded-lg">
 <h3 class="text-xl font-semibold mb-4">🎲 Dice Roll</h3>
 <div class="space-y-4">
 <!-- Dice Display -->
 <div class="dice-display bg-gray-900 p-6 rounded-lg border-4 border-red-600">
 <div id="diceAnimation" class="flex justify-center items-center text-8xl mb-4">
 🎲
 </div>
 <div class="text-center">
 <div class="text-sm text-gray-400">Predict the number (1-6)</div>
 <div class="text-sm text-gray-300">Exact match = 5x your bet!</div>
 </div>
 </div>
 <!-- Controls -->
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">User ID</label>
 <input type="text" 
 id="diceUserId" 
 placeholder="Enter User ID" 
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
 value="${this.state.diceUserId}">
 </div>
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">Bet Amount</label>
 <input type="number" 
 id="diceBet" 
 placeholder="Bet Amount" 
 min="${this.options.minBetAmount}"
 max="${this.options.maxBetAmount}"
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500"
 value="${this.state.diceBet}">
 </div>
 <div class="form-group">
 <label class="block text-sm font-medium mb-2">Prediction (1-6)</label>
 <select id="dicePrediction" 
 class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500">
 ${[1,2,3,4,5,6].map(num => 
 `<option value="${num}" ${this.state.dicePrediction === num ? 'selected' : ''}>${num}</option>`
 ).join('')}</select>
 </div>
 <button id="rollDiceBtn" 
 class="w-full bg-red-600 hover:bg-red-700 p-3 rounded font-medium">
 🎲 ROLL!
 </button>
 <div id="diceResult" class="text-center min-h-[80px]">
 <!-- Results will appear here -->
 </div>
 </div>
 </div>
 `;}renderHistorySection(){return `
 <div class="mt-6 bg-gray-800 p-6 rounded-lg">
 <h3 class="text-xl font-semibold mb-4">📈 Recent Games</h3>
 <div id="gamblingHistory" class="overflow-x-auto">
 <!-- History will be populated here -->
 </div>
 </div>
 `;}bindEvents(){if(this.options.enableSlots){const spinBtn = this.container.querySelector('#spinSlotsBtn');const slotsUserInput = this.container.querySelector('#slotsUserId');const slotsBetInput = this.container.querySelector('#slotsBet');this.addEventListener(spinBtn,'click',() => this.playSlots());this.addEventListener(slotsUserInput,'input',(e) =>{this.setState({slotsUserId: e.target.value});});this.addEventListener(slotsBetInput,'input',(e) =>{this.setState({slotsBet: parseInt(e.target.value) || 0});});}if(this.options.enableCoinflip){const flipBtn = this.container.querySelector('#flipCoinBtn');const coinflipUserInput = this.container.querySelector('#coinflipUserId');const coinflipBetInput = this.container.querySelector('#coinflipBet');const coinflipChoiceSelect = this.container.querySelector('#coinflipChoice');this.addEventListener(flipBtn,'click',() => this.playCoinflip());this.addEventListener(coinflipUserInput,'input',(e) =>{this.setState({coinflipUserId: e.target.value});});this.addEventListener(coinflipBetInput,'input',(e) =>{this.setState({coinflipBet: parseInt(e.target.value) || 0});});this.addEventListener(coinflipChoiceSelect,'change',(e) =>{this.setState({coinflipChoice: e.target.value});});}if(this.options.enableDice){const rollBtn = this.container.querySelector('#rollDiceBtn');const diceUserInput = this.container.querySelector('#diceUserId');const diceBetInput = this.container.querySelector('#diceBet');const dicePredictionSelect = this.container.querySelector('#dicePrediction');this.addEventListener(rollBtn,'click',() => this.playDice());this.addEventListener(diceUserInput,'input',(e) =>{this.setState({diceUserId: e.target.value});});this.addEventListener(diceBetInput,'input',(e) =>{this.setState({diceBet: parseInt(e.target.value) || 0});});this.addEventListener(dicePredictionSelect,'change',(e) =>{this.setState({dicePrediction: parseInt(e.target.value)});});}this.eventBus.on('economy:balance-updated',(data) => this.onBalanceUpdated(data));}async loadData(){try{this.setState({loading: true,error: null});await Promise.all([
 this.loadStats(),this.loadLeaderboard(),this.loadHistory()
 ]);this.setState({loading: false});}catch (error){this.handleError(error);}}async playSlots(){const{slotsUserId,slotsBet}= this.state;if(!this.validateGameInput(slotsUserId,slotsBet,'slots')){return;}if(this.state.slotsSpinning){return;}try{this.setState({slotsSpinning: true});this.animateSlots();const result = await this.api.gambling.playSlots({userId: slotsUserId,bet: slotsBet});if(result.success){setTimeout(() =>{this.setState({slotsResult: result,slotsSpinning: false});this.displaySlotsResult(result);this.eventBus.emit('gambling:game-played',{game: 'slots',userId: slotsUserId,result});},this.options.animationDuration);}else{this.setState({slotsSpinning: false});this.showNotification(result.error || 'Slots game failed','error');}}catch (error){this.setState({slotsSpinning: false});this.handleError(error);}}async playCoinflip(){const{coinflipUserId,coinflipBet,coinflipChoice}= this.state;if(!this.validateGameInput(coinflipUserId,coinflipBet,'coinflip')){return;}if(this.state.coinflipFlipping){return;}try{this.setState({coinflipFlipping: true});this.animateCoinflip();const result = await this.api.gambling.playCoinflip({userId: coinflipUserId,amount: coinflipBet,choice: coinflipChoice});if(result.success){setTimeout(() =>{this.setState({coinflipResult: result,coinflipFlipping: false});this.displayCoinflipResult(result);this.eventBus.emit('gambling:game-played',{game: 'coinflip',userId: coinflipUserId,result});},this.options.animationDuration);}else{this.setState({coinflipFlipping: false});this.showNotification(result.error || 'Coinflip game failed','error');}}catch (error){this.setState({coinflipFlipping: false});this.handleError(error);}}async playDice(){const{diceUserId,diceBet,dicePrediction}= this.state;if(!this.validateGameInput(diceUserId,diceBet,'dice')){return;}if(this.state.diceRolling){return;}try{this.setState({diceRolling: true});this.animateDice();const result = await this.api.gambling.playDice({userId: diceUserId,amount: diceBet,prediction: dicePrediction});if(result.success){setTimeout(() =>{this.setState({diceResult: result,diceRolling: false});this.displayDiceResult(result);this.eventBus.emit('gambling:game-played',{game: 'dice',userId: diceUserId,result});},this.options.animationDuration);}else{this.setState({diceRolling: false});this.showNotification(result.error || 'Dice game failed','error');}}catch (error){this.setState({diceRolling: false});this.handleError(error);}}validateGameInput(userId,betAmount,gameType){if(!userId.trim()){this.showNotification('Please enter a user ID','warning');return false;}if(!betAmount || betAmount < this.options.minBetAmount){this.showNotification(`Minimum bet is ${this.options.minBetAmount}`,'warning');return false;}if(betAmount > this.options.maxBetAmount){this.showNotification(`Maximum bet is ${this.options.maxBetAmount}`,'warning');return false;}return true;}animateSlots(){const reels = this.container.querySelectorAll('.reel');const symbols = ['🍒','🍋','🔔','⭐','💎'];reels.forEach(reel =>{let count = 0;const interval = setInterval(() =>{reel.textContent = symbols[Math.floor(Math.random() * symbols.length)];count++;if(count >= 20){clearInterval(interval);}},100);});}animateCoinflip(){const coin = this.container.querySelector('#coinAnimation');const symbols = ['🟡','⚪'];let count = 0;const interval = setInterval(() =>{coin.textContent = symbols[count % 2];count++;if(count >= 20){clearInterval(interval);}},100);}animateDice(){const dice = this.container.querySelector('#diceAnimation');const symbols = ['⚀','⚁','⚂','⚃','⚄','⚅'];let count = 0;const interval = setInterval(() =>{dice.textContent = symbols[Math.floor(Math.random() * symbols.length)];count++;if(count >= 20){clearInterval(interval);}},100);}displaySlotsResult(result){const resultDiv = this.container.querySelector('#slotsResult');const reels = this.container.querySelectorAll('.reel');result.result.forEach((symbol,index) =>{if(reels[index]){reels[index].textContent = symbol;}});const isWin = result.net_change > 0;resultDiv.innerHTML = `
 <div class="result-display p-4 rounded ${isWin ? 'bg-green-800 border border-green-600' : 'bg-red-800 border border-red-600'}">
 <div class="text-2xl mb-2">${result.result.join(' ')}</div>
 <div class="text-lg font-bold ${isWin ? 'text-green-400' : 'text-red-400'}">
 ${isWin ? '🎉 Won' : '💸 Lost'}: ${Math.abs(result.net_change).toLocaleString()}coins
 </div>
 <div class="text-sm text-gray-300 mt-2">
 New Balance: ${result.new_balance.toLocaleString()}coins
 </div>
 </div>
 `;}displayCoinflipResult(result){const resultDiv = this.container.querySelector('#coinflipResult');const coin = this.container.querySelector('#coinAnimation');coin.textContent = result.result === 'heads' ? '🟡' : '⚪';const isWin = result.won;resultDiv.innerHTML = `
 <div class="result-display p-4 rounded ${isWin ? 'bg-green-800 border border-green-600' : 'bg-red-800 border border-red-600'}">
 <div class="text-lg mb-2">
 Result: <span class="text-2xl">${result.result === 'heads' ? '🟡 Heads' : '⚪ Tails'}</span>
 </div>
 <div class="text-lg font-bold ${isWin ? 'text-green-400' : 'text-red-400'}">
 ${isWin ? '🎉 Won' : '💸 Lost'}: ${Math.abs(result.net_change).toLocaleString()}coins
 </div>
 <div class="text-sm text-gray-300 mt-2">
 New Balance: ${result.new_balance.toLocaleString()}coins
 </div>
 </div>
 `;}displayDiceResult(result){const resultDiv = this.container.querySelector('#diceResult');const dice = this.container.querySelector('#diceAnimation');const diceSymbols = ['⚀','⚁','⚂','⚃','⚄','⚅'];dice.textContent = diceSymbols[result.result - 1];const isWin = result.won;resultDiv.innerHTML = `
 <div class="result-display p-4 rounded ${isWin ? 'bg-green-800 border border-green-600' : 'bg-red-800 border border-red-600'}">
 <div class="text-lg mb-2">
 Rolled: <span class="text-2xl">${result.result}</span>
 </div>
 <div class="text-sm mb-2">
 Your prediction: ${result.prediction}</div>
 <div class="text-lg font-bold ${isWin ? 'text-green-400' : 'text-red-400'}">
 ${isWin ? '🎉 Won' : '💸 Lost'}: ${Math.abs(result.net_change).toLocaleString()}coins
 </div>
 <div class="text-sm text-gray-300 mt-2">
 New Balance: ${result.new_balance.toLocaleString()}coins
 </div>
 </div>
 `;}async loadStats(){try{const stats ={totalGames: 0,totalWagered: 0,totalWon: 0,houseEdge: 0};this.setState({stats});this.renderStats(stats);}catch (error){console.error('Failed to load gambling stats:',error);}}async loadLeaderboard(){try{const leaderboard = await this.api.gambling.getLeaderboard();this.setState({leaderboard});this.renderLeaderboard(leaderboard);}catch (error){console.error('Failed to load gambling leaderboard:',error);}}async loadHistory(){try{const history = [];this.setState({history});this.renderHistory(history);}catch (error){console.error('Failed to load gambling history:',error);}}renderStats(stats){const statsContainer = this.container.querySelector('#gamblingStats');if(statsContainer){statsContainer.innerHTML = `
 <div class="grid grid-cols-2 gap-4">
 <div class="text-center">
 <div class="text-lg font-bold">${stats.totalGames || 0}</div>
 <div class="text-sm text-gray-400">Total Games</div>
 </div>
 <div class="text-center">
 <div class="text-lg font-bold">${(stats.totalWagered || 0).toLocaleString()}</div>
 <div class="text-sm text-gray-400">Total Wagered</div>
 </div>
 </div>
 `;}}renderLeaderboard(leaderboard){const leaderboardContainer = this.container.querySelector('#gamblingLeaderboard');if(leaderboardContainer){if(leaderboard.length === 0){leaderboardContainer.innerHTML = '<div class="text-gray-400 text-center py-4">No games played yet</div>';return;}leaderboardContainer.innerHTML = leaderboard.slice(0,5).map((user,index) => `
 <div class="flex items-center justify-between p-2 bg-gray-700 rounded mb-2">
 <div class="flex items-center space-x-2">
 <span class="font-bold ${index === 0 ? 'text-yellow-400' : 'text-gray-400'}">
 ${index + 1}</span>
 <span>${user.userId}</span>
 </div>
 <span class="text-green-400 text-sm">${user.total_profit > 0 ? '+' : ''}${user.total_profit}</span>
 </div>
 `).join('');}}renderHistory(history){const historyContainer = this.container.querySelector('#gamblingHistory');if(historyContainer){if(history.length === 0){historyContainer.innerHTML = '<div class="text-gray-400 text-center py-4">No recent games</div>';return;}historyContainer.innerHTML = '<div class="text-gray-400 text-center py-4">History feature coming soon</div>';}}onBalanceUpdated(data){}showNotification(message,type = 'info'){this.eventBus.emit('notification:show',{message,type});}onDestroy(){this.eventBus.off('economy:balance-updated');}}if(typeof module !== 'undefined' && module.exports){module.exports = GamblingComponent;}else{window.GamblingComponent = GamblingComponent;}