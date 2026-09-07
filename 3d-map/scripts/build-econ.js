#!/usr/bin/env node
// Inline data/econ.json into the map. Usage: node scripts/build-econ.js
const fs=require('fs'), path=require('path');
const root=path.join(__dirname,'..');
const html=path.join(root,'europe-economic-map-textured.html');
const data=JSON.parse(fs.readFileSync(path.join(root,'data/econ.json'),'utf8'));
const N=data.meta.years.length, problems=[];
for(const [c,d] of Object.entries(data.countries)) for(const k of ['gdp','pc','pop','src'])
  if(!Array.isArray(d[k])||d[k].length!==N) problems.push(c+'.'+k+' must have '+N+' entries');
if(problems.length){ console.error(problems.join('\n')); process.exit(1); }
const lines=fs.readFileSync(html,'utf8').split('\n');
const i=lines.findIndex(l=>l.startsWith('const ECON_V2 = '));
if(i<0){ console.error('const ECON_V2 line not found'); process.exit(1); }
lines[i]='const ECON_V2 = '+JSON.stringify(data)+'; // generated from data/econ.json by scripts/build-econ.js — do not edit by hand';
fs.writeFileSync(html,lines.join('\n'));
console.log('inlined data/econ.json →',path.basename(html),'('+Object.keys(data.countries).length+' countries, '+N+' years)');
