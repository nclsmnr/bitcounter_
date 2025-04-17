#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def main():
    html_content = '''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BITCOUNTER - Bitcoin Liquidity Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/luxon@3.0.1"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.2.0"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --primary: #f7931a;
            --secondary: #1a1a2e;
            --accent: #4cc2ff;
            --dark: #0f0f1a;
            --light: #f8f9fa;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--dark);
            color: var(--light);
        }
        
        .mono {
            font-family: 'Space Mono', monospace;
        }
        
        .card {
            background: rgba(26, 26, 46, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }
        
        .price-up {
            color: #00ff9d;
        }
        
        .price-down {
            color: #ff3a3a;
        }
        
        .progress-bar {
            height: 6px;
            border-radius: 3px;
            background: rgba(255, 255, 255, 0.1);
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #f7931a, #ffc107);
            border-radius: 3px;
        }
        
        .countdown {
            font-size: 1.5rem;
            font-weight: bold;
            background: linear-gradient(135deg, #f7931a, #e14a32);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .tradingview-widget-container {
            height: 500px;
            width: 100%;
        }
        
        @media (max-width: 768px) {
            .tradingview-widget-container {
                height: 300px;
            }
        }
        
        .news-card {
            transition: all 0.3s ease;
        }
        
        .news-card:hover {
            background: rgba(79, 79, 134, 0.3);
        }
        
        .fear-greed {
            height: 120px;
            width: 120px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2rem;
            margin: 0 auto;
        }
        
        /* Spinner */
        .spinner {
            width: 24px;
            height: 24px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #f7931a;
            animation: spin 1s ease-in-out infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <header class="flex flex-col md:flex-row justify-between items-center mb-8">
            <div class="flex items-center mb-4 md:mb-0">
                <i class="fab fa-bitcoin text-4xl text-orange-500 mr-3"></i>
                <h1 class="text-3xl font-bold text-white">
                    <span class="text-orange-500">BIT</span>COUNTER
                </h1>
                <span class="ml-2 px-2 py-1 bg-orange-500 text-xs rounded-md">v1.0</span>
            </div>
            
            <div class="flex items-center">
                <div class="mr-4">
                    <div class="text-sm text-gray-400">Prezzo BTC</div>
                    <div class="text-2xl font-bold mono" id="btc-price-container">
                        <span id="btc-price">$00,000.00</span>
                        <span id="price-change-indicator" class="ml-2 text-sm"></span>
                    </div>
                </div>
                <div class="mr-4">
                    <div class="text-sm text-gray-400">Variazione 24h</div>
                    <div class="text-xl mono" id="btc-change">+0.00%</div>
                </div>
                <div class="hidden md:block">
                    <div class="text-sm text-gray-400">Dominanza</div>
                    <div class="text-xl mono" id="btc-dominance">00.0%</div>
                </div>
            </div>
        </header>
        
        <!-- Main Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <!-- Sezione A: Calcoli e stime -->
            <div class="lg:col-span-1">
                <div class="card rounded-xl p-6 h-full">
                    <h2 class="text-xl font-bold mb-4 text-orange-500 flex items-center">
                        <i class="fas fa-calculator mr-2"></i> Calcoli e Stime
                    </h2>
                    
                    <div class="space-y-4">
                        <div>
                            <div class="flex justify-between text-sm mb-1">
                                <span class="text-gray-400">Supply Massima</span>
                                <span class="mono">21,000,000 BTC</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" id="supply-progress" style="width: 0%"></div>
                            </div>
                        </div>
                        
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Supply Emessa</div>
                                <div class="text-lg mono" id="circulating-supply">Loading...</div>
                            </div>
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Supply Liquida</div>
                                <div class="text-lg mono" id="liquid-supply">Loading...</div>
                            </div>
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">BTC Irrecuperabili</div>
                                <div class="text-lg mono" id="lost-btc">Loading...</div>
                            </div>
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Inflation Rate</div>
                                <div class="text-lg mono" id="inflation-rate">Loading...</div>
                            </div>
                        </div>
                        
                        <div class="pt-4 border-t border-gray-700">
                            <h3 class="text-md font-semibold mb-3 text-gray-300">Modelli di Prezzo</h3>
                            <div class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <span class="text-sm text-gray-400">Stock-to-Flow</span>
                                    <span class="mono" id="s2f-price">Loading...</span>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-sm text-gray-400">Metcalfe Law</span>
                                    <span class="mono" id="metcalfe-price">Loading...</span>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-sm text-gray-400">NVT Ratio</span>
                                    <span class="mono" id="nvt-price">Loading...</span>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-sm text-gray-400">Ratio-Basic</span>
                                    <span class="mono" id="ratio-price">Loading...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Sezione B: Statistiche di rete -->
            <div class="lg:col-span-1">
                <div class="card rounded-xl p-6 h-full">
                    <h2 class="text-xl font-bold mb-4 text-orange-500 flex items-center">
                        <i class="fas fa-network-wired mr-2"></i> Statistiche di Rete
                    </h2>
                    
                    <div class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Block Height</div>
                                <div class="text-lg mono" id="block-height">Loading...</div>
                            </div>
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Difficoltà</div>
                                <div class="text-lg mono" id="difficulty">Loading...</div>
                            </div>
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Hashrate</div>
                                <div class="text-lg mono" id="hashrate">Loading...</div>
                            </div>
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Tempo Blocco</div>
                                <div class="text-lg mono" id="block-time">Loading...</div>
                            </div>
                        </div>
                        
                        <div class="pt-4 border-t border-gray-700">
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-sm text-gray-400">Prossimo Halving</span>
                                <span class="text-sm mono" id="next-halving">Loading...</span>
                            </div>
                            <div class="progress-bar mb-2">
                                <div class="progress-fill" id="halving-progress" style="width: 0%"></div>
                            </div>
                            <div class="text-center countdown mono" id="halving-countdown">Loading...</div>
                        </div>
                        
                        <div class="pt-4 border-t border-gray-700">
                            <h3 class="text-md font-semibold mb-3 text-gray-300">Reward Attuale</h3>
                            <div class="flex items-center justify-between">
                                <div class="flex items-center">
                                    <i class="fas fa-coins text-yellow-500 mr-2"></i>
                                    <span class="mono" id="block-reward">Loading...</span>
                                </div>
                                <div class="text-sm text-gray-400">~$<span id="block-reward-usd">Loading...</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Sezione C: Transazioni e mempool -->
            <div class="lg:col-span-1">
                <div class="card rounded-xl p-6 h-full">
                    <h2 class="text-xl font-bold mb-4 text-orange-500 flex items-center">
                        <i class="fas fa-exchange-alt mr-2"></i> Transazioni e Mempool
                    </h2>
                    
                    <div class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">TX in Mempool</div>
                                <div class="text-lg mono" id="mempool-tx">Loading...</div>
                            </div>
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Dimensione Mempool</div>
                                <div class="text-lg mono" id="mempool-size">Loading...</div>
                            </div>
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Fee Media</div>
                                <div class="text-lg mono" id="avg-fee">Loading...</div>
                            </div>
                            <div class="bg-gray-800 rounded-lg p-3">
                                <div class="text-xs text-gray-400">Ultimo Blocco</div>
                                <div class="text-lg mono" id="last-block-tx">Loading...</div>
                            </div>
                        </div>
                        
                        <div class="pt-4 border-t border-gray-700">
                            <h3 class="text-md font-semibold mb-3 text-gray-300">Fee Priorità</h3>
                            <div class="space-y-2">
                                <div class="flex justify-between items-center text-sm">
                                    <span class="text-gray-400">Alta</span>
                                    <span class="mono" id="high-fee">Loading...</span>
                                </div>
                                <div class="flex justify-between items-center text-sm">
                                    <span class="text-gray-400">Media</span>
                                    <span class="mono" id="medium-fee">Loading...</span>
                                </div>
                                <div class="flex justify-between items-center text-sm">
                                    <span class="text-gray-400">Bassa</span>
                                    <span class="mono" id="low-fee">Loading...</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="pt-4 border-t border-gray-700">
                            <h3 class="text-md font-semibold mb-3 text-gray-300">Ultime Transazioni</h3>
                            <div class="space-y-2 max-h-40 overflow-y-auto pr-2" id="recent-transactions">
                                <div class="spinner"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <!-- resto del codice HTML... -->
    </div>
</body>
</html>'''
    print(html_content)

if __name__ == '__main__':
    main()

