import os

path = 'c:/Users/Divvyansh Kudesiaa/Desktop/Sentinel/frontend/script.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# REPLACEMENT 1: pipe-climate-card
climate_old = '''    const pipeClimate = document.getElementById('pipe-climate-card');
    if (pipeClimate) {
        pipeClimate.innerHTML = 
            <h4 class=\x22panel-title\x22 style=\x22font-size: 0.8rem\x22>Climate Analysis Radar</h4>
            <div class=\x22radar-container\x22>
                <svg width=\x22160\x22 height=\x22160\x22 viewBox=\x220 0 160 160\x22>
                    <polygon points=\x2280,10 146,57 121,136 39,136 14,57\x22 fill=\x22none\x22 stroke=\x22rgba(255,255,255,0.05)\x22 />
                    <polygon points=\x2280,30 126,63 111,116 49,116 34,63\x22 fill=\x22none\x22 stroke=\x22rgba(255,255,255,0.05)\x22 />
                    <polygon points=\x2280,50 106,69 99,96 61,96 54,69\x22 fill=\x22none\x22 stroke=\x22rgba(255,255,255,0.05)\x22 />
                    <polygon points=\x2280,25 130,65 110,120 50,110 25,60\x22 fill=\x22rgba(168, 255, 62, 0.2)\x22 stroke=\x22var(--neon-lime)\x22 stroke-width=\x222\x22 />
                </svg>
            </div>
            <div style=\x22display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:0.7rem; color:var(--muted-text); margin-top:1rem\x22>
                <span>Carbon: </span>
                <span>Water: </span>
                <span>Gov: </span>
                <span>Social: </span>
            </div>
        ;
    }'''

climate_new = '''    const pipeClimate = document.getElementById('pipe-climate-card');
    if (pipeClimate) {
        const carbonScore = c.green_score || 82;
        const waterScore = Math.floor(Math.random() * 50 + 30);
        const govScore = Math.floor(Math.random() * 20 + 70);
        const socialScore = Math.floor(Math.random() * 20 + 60);
        
        const r1 = (carbonScore/100)*60;
        const r2 = (waterScore/100)*60;
        const r3 = (govScore/100)*60;
        const r4 = (socialScore/100)*60;
        const radarPolygon = 80, ,80 80, ,80;

        pipeClimate.innerHTML = 
            <h4 class=\x22panel-title\x22 style=\x22font-size: 0.8rem\x22>Climate Analysis Radar</h4>
            <div class=\x22radar-container\x22>
                <svg width=\x22160\x22 height=\x22160\x22 viewBox=\x220 0 160 160\x22>
                    <polygon points=\x2280,20 140,80 80,140 20,80\x22 fill=\x22none\x22 stroke=\x22rgba(255,255,255,0.05)\x22 />
                    <polygon points=\x2280,40 120,80 80,120 40,80\x22 fill=\x22none\x22 stroke=\x22rgba(255,255,255,0.05)\x22 />
                    <polygon points=\x2280,60 100,80 80,100 60,80\x22 fill=\x22none\x22 stroke=\x22rgba(255,255,255,0.05)\x22 />
                    <polygon points=\x22\x22 fill=\x22rgba(168, 255, 62, 0.2)\x22 stroke=\x22var(--neon-lime)\x22 stroke-width=\x222\x22 />
                </svg>
            </div>
            <div style=\x22display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:0.7rem; color:var(--muted-text); margin-top:1rem\x22>
                <span>Carbon: </span>
                <span>Water: </span>
                <span>Gov: </span>
                <span>Social: </span>
            </div>
        ;
    }'''

content = content.replace(climate_old, climate_new)

# REPLACEMENT 2: pipe-financial-card
fin_old = '''    const pipeFinancial = document.getElementById('pipe-financial-card');
    if (pipeFinancial) {
        const retPct = f.expected_return ? (f.expected_return * 100).toFixed(1) : 0;
        pipeFinancial.innerHTML = 
            <h4 class=\x22panel-title\x22 style=\x22font-size: 0.8rem\x22>Financial Indicators</h4>
            <div style=\x22margin: 1.5rem 0\x22>
                <div style=\x22display:flex; justify-content:space-between; margin-bottom:12px\x22>
                    <span style=\x22font-size:0.8rem\x22>Est Return</span>
                    <span style=\x22font-weight:700; color:#00ff88\x22>%</span>
                </div>
                <div style=\x22display:flex; justify-content:space-between; margin-bottom:12px\x22>
                    <span style=\x22font-size:0.8rem\x22>Sentiment</span>
                    <span style=\x22font-weight:700\x22></span>
                </div>
                <!-- Mini Candlestick Visual -->
                <div style=\x22display:flex; align-items:flex-end; gap:8px; height:60px; margin-bottom:15px\x22>
                    <div style=\x22width:8px; height:30px; background:#ff4444; position:relative;\x22><div style=\x22width:2px; height:45px; background:#ff4444; position:absolute; left:3px; top:-7px;\x22></div></div>
                    <div style=\x22width:8px; height:40px; background:#00ff88; position:relative;\x22><div style=\x22width:2px; height:55px; background:#00ff88; position:absolute; left:3px; top:-7px;\x22></div></div>
                    <div style=\x22width:8px; height:20px; background:#00ff88; position:relative;\x22><div style=\x22width:2px; height:35px; background:#00ff88; position:absolute; left:3px; top:-7px;\x22></div></div>
                    <div style=\x22width:8px; height:35px; background:#00ff88; position:relative;\x22><div style=\x22width:2px; height:50px; background:#00ff88; position:absolute; left:3px; top:-7px;\x22></div></div>
                    <div style=\x22width:8px; height:15px; background:#ff4444; position:relative;\x22><div style=\x22width:2px; height:30px; background:#ff4444; position:absolute; left:3px; top:-7px;\x22></div></div>
                </div>
                <div style=\x22display:flex; gap:4px\x22>
                    <div style=\x22flex:1; height:4px; background:#00ff88;\x22></div>
                    <div style=\x22flex:1; height:4px; background:#00ff88;\x22></div>
                    <div style=\x22flex:1; height:4px; background:#ffcc00;\x22></div>
                    <div style=\x22flex:1; height:4px; background:rgba(255,255,255,0.1);\x22></div>
                </div>
                <span style=\x22font-size:0.6rem; color:var(--muted-text); margin-top:5px; display:block;\x22>MOMENTUM INDICATOR</span>
            </div>
        ;
    }'''
fin_new = '''    const pipeFinancial = document.getElementById('pipe-financial-card');
    if (pipeFinancial) {
        const retPct = f.expected_return ? (f.expected_return * 100).toFixed(1) : 0;
        
        let candleHTML = '';
        const numCandles = 5;
        const isPositive = (f.expected_return || 0) >= 0;
        for (let i=0; i<numCandles; i++) {
            const isUp = i === numCandles - 1 ? isPositive : (Math.random() > 0.5);
            const height = Math.max(10, Math.random() * 40 + 10);
            const wickHeight = height + Math.random() * 20;
            const topOffset = - (wickHeight - height) / 2;
            const bg = isUp ? '#00ff88' : '#ff4444';
            candleHTML += <div style=\x22width:8px; height:px; background:; position:relative;\x22><div style=\x22width:2px; height:px; background:; position:absolute; left:3px; top:px;\x22></div></div>;
        }

        pipeFinancial.innerHTML = 
            <h4 class=\x22panel-title\x22 style=\x22font-size: 0.8rem\x22>Financial Indicators</h4>
            <div style=\x22margin: 1.5rem 0\x22>
                <div style=\x22display:flex; justify-content:space-between; margin-bottom:12px\x22>
                    <span style=\x22font-size:0.8rem\x22>Est Return</span>
                    <span style=\x22font-weight:700; color:#00ff88\x22>%</span>
                </div>
                <div style=\x22display:flex; justify-content:space-between; margin-bottom:12px\x22>
                    <span style=\x22font-size:0.8rem\x22>Sentiment</span>
                    <span style=\x22font-weight:700\x22></span>
                </div>
                <!-- Dynamic Candlestick Visual -->
                <div style=\x22display:flex; align-items:flex-end; gap:8px; height:60px; margin-bottom:15px\x22>
                    
                </div>
                <div style=\x22display:flex; gap:4px\x22>
                    <div style=\x22flex:1; height:4px; background:#00ff88;\x22></div>
                    <div style=\x22flex:1; height:4px; background:#00ff88;\x22></div>
                    <div style=\x22flex:1; height:4px; background:#ffcc00;\x22></div>
                    <div style=\x22flex:1; height:4px; background:rgba(255,255,255,0.1);\x22></div>
                </div>
                <span style=\x22font-size:0.6rem; color:var(--muted-text); margin-top:5px; display:block;\x22>MOMENTUM INDICATOR</span>
            </div>
        ;
    }'''
content = content.replace(fin_old, fin_new)

# REPLACEMENT 3: pipe-simulation-card
sim_old = '''    const pipeSim = document.getElementById('pipe-simulation-card');
    if (pipeSim) {
        const drawdown = sim.drawdown_probability ? (sim.drawdown_probability * 100).toFixed(1) : 0;
        pipeSim.innerHTML = 
            <h4 class=\x22panel-title\x22 style=\x22font-size: 0.8rem\x22>Monte Carlo Simulation</h4>
            <div class=\x22monte-carlo-container\x22>
                <svg width=\x22100%\x22 height=\x22160\x22 preserveAspectRatio=\x22none\x22>
                    <path d=\x22M0 100 Q 50 80 300 130\x22 fill=\x22none\x22 stroke=\x22rgba(168, 255, 62, 0.05)\x22 />
                    <path d=\x22M0 100 Q 80 50 300 40\x22 fill=\x22none\x22 stroke=\x22rgba(168, 255, 62, 0.05)\x22 />
                    <path d=\x22M0 100 Q 120 120 300 110\x22 fill=\x22none\x22 stroke=\x22rgba(168, 255, 62, 0.05)\x22 />
                    <path d=\x22M0 100 Q 150 70 300 20\x22 fill=\x22none\x22 stroke=\x22rgba(168, 255, 62, 0.05)\x22 />
                    <path d=\x22M0 100 Q 200 150 300 140\x22 fill=\x22none\x22 stroke=\x22rgba(168, 255, 62, 0.05)\x22 />
                    <path d=\x22M0 100 Q 150 80 300 70\x22 fill=\x22none\x22 stroke=\x22var(--neon-lime)\x22 stroke-width=\x222\x22 />
                    <path d=\x22M0 100 Q 150 40 300 30 L 300 120 Q 150 110 0 100\x22 fill=\x22rgba(168, 255, 62, 0.03)\x22 />
                </svg>
            </div>
            <div style=\x22font-size:0.75rem; text-align:center; margin-top:10px\x22>
                Drawdown Probability: <b style=\x22color:#ffcc00\x22>%</b><br>
                <span style=\x22color:var(--muted-text);font-size:0.7rem\x22>Estimated Value: </span>
            </div>
        ;
    }'''
sim_new = '''    const pipeSim = document.getElementById('pipe-simulation-card');
    if (pipeSim) {
        let pathsHtml = '';
        const endYBase = sim.expected_1y_value && p.total_budget ? 100 - ((sim.expected_1y_value - p.total_budget) / p.total_budget)*100 : 70; 
        
        for(let i=0; i<5; i++) {
            const endY = endYBase + (Math.random()-0.5)*80;
            const ctrlX = 150 + (Math.random()-0.5)*50;
            const ctrlY = 100 + (Math.random()-0.5)*100;
            pathsHtml += <path d=\x22M0 100 Q   300 \x22 fill=\x22none\x22 stroke=\x22rgba(168, 255, 62, 0.05)\x22 />;
        }
        pathsHtml += <path d=\x22M0 100 Q 150 100 300 \x22 fill=\x22none\x22 stroke=\x22var(--neon-lime)\x22 stroke-width=\x222\x22 />;
        pathsHtml += <path d=\x22M0 100 Q 150 40 300  L 300  Q 150 110 0 100\x22 fill=\x22rgba(168, 255, 62, 0.03)\x22 />;

        const drawdown = sim.drawdown_probability ? (sim.drawdown_probability * 100).toFixed(1) : 0;
        pipeSim.innerHTML = 
            <h4 class=\x22panel-title\x22 style=\x22font-size: 0.8rem\x22>Monte Carlo Simulation</h4>
            <div class=\x22monte-carlo-container\x22>
                <svg width=\x22100%\x22 height=\x22160\x22 preserveAspectRatio=\x22none\x22>
                    
                </svg>
            </div>
            <div style=\x22font-size:0.75rem; text-align:center; margin-top:10px\x22>
                Drawdown Probability: <b style=\x22color:#ffcc00\x22>%</b><br>
                <span style=\x22color:var(--muted-text);font-size:0.7rem\x22>Estimated Value: </span>
            </div>
        ;
    }'''
content = content.replace(sim_old, sim_new)

# REPLACEMENT 4: pipe-allocation-card
alloc_old = '''    const pipeAllocation = document.getElementById('pipe-allocation-card');
    if (pipeAllocation) {
        const holdingsText = (p.holdings || []).map(h => ${h.ticker}: %).join(' | ');
        pipeAllocation.innerHTML = 
             <h4 class=\x22panel-title\x22 style=\x22font-size: 0.8rem\x22>Allocation Weight</h4>
             <div class=\x22donut-container\x22 style=\x22width:140px; height:140px; margin: 0 auto;\x22>
                <svg width=\x22120\x22 height=\x22120\x22 viewBox=\x220 0 120 120\x22>
                    <circle r=\x2245\x22 cx=\x2260\x22 cy=\x2260\x22 fill=\x22transparent\x22 stroke=\x22#a8ff3e\x22 stroke-width=\x2212\x22 stroke-dasharray=\x22113.1 282.7\x22 stroke-dashoffset=\x220\x22 />
                    <circle r=\x2245\x22 cx=\x2260\x22 cy=\x2260\x22 fill=\x22transparent\x22 stroke=\x22#00d2ff\x22 stroke-width=\x2212\x22 stroke-dasharray=\x2279.2 282.7\x22 stroke-dashoffset=\x22-113.1\x22 />
                    <circle r=\x2245\x22 cx=\x2260\x22 cy=\x2260\x22 fill=\x22transparent\x22 stroke=\x22#ffd200\x22 stroke-width=\x2212\x22 stroke-dasharray=\x2290.5 282.7\x22 stroke-dashoffset=\x22-192.3\x22 />
                </svg>
             </div>
             <div style=\x22font-size:0.7rem; color:var(--muted-text); text-align:center; margin-top:10px\x22></div>
        ;
    }'''
alloc_new = '''    const pipeAllocation = document.getElementById('pipe-allocation-card');
    if (pipeAllocation) {
        const holdings = p.holdings || [];
        const colors = ['#a8ff3e', '#00d2ff', '#ffd200', '#ff4444', '#b026ff'];
        let svgCircles = '';
        let offset = 0;
        const circumference = 282.7;
        
        if (holdings.length === 0) {
            svgCircles = <circle r=\x2245\x22 cx=\x2260\x22 cy=\x2260\x22 fill=\x22transparent\x22 stroke=\x22#333\x22 stroke-width=\x2212\x22 stroke-dasharray=\x22282.7 282.7\x22 stroke-dashoffset=\x220\x22 />;
        } else {
            holdings.forEach((h, i) => {
                const strokeArr = Math.max(0.1, (h.weight * circumference)).toFixed(1);
                svgCircles += <circle r=\x2245\x22 cx=\x2260\x22 cy=\x2260\x22 fill=\x22transparent\x22 stroke=\x22\x22 stroke-width=\x2212\x22 stroke-dasharray=\x22 282.7\x22 stroke-dashoffset=\x22\x22 />;
                offset += (h.weight * circumference);
            });
        }
        
        const holdingsText = holdings.map(h => ${h.ticker}: %).join(' | ');
        pipeAllocation.innerHTML = 
             <h4 class=\x22panel-title\x22 style=\x22font-size: 0.8rem\x22>Allocation Weight</h4>
             <div class=\x22donut-container\x22 style=\x22width:140px; height:140px; margin: 0 auto;\x22>
                <svg width=\x22120\x22 height=\x22120\x22 viewBox=\x220 0 120 120\x22>
                    
                </svg>
             </div>
             <div style=\x22font-size:0.7rem; color:var(--muted-text); text-align:center; margin-top:10px\x22></div>
        ;
    }'''
content = content.replace(alloc_old, alloc_new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print( Updated successfully)
