// Evaluate and capture the same scenegraph used for the exported SVG.
// No formatted label parsing and no reference relation is accepted.
import fs from 'node:fs';
import * as vega from 'vega';

const spec = JSON.parse(fs.readFileSync(0, 'utf8'));
const errors = [], warnings = [];
const logger = {level: () => 0, error: (...x) => errors.push(x.map(String).join(' ')),
  warn: (...x) => warnings.push(x.map(String).join(' ')), info: () => {}, debug: () => {}};
const loader = {load: async () => {throw Error('External data loading is disabled');},
  sanitize: async () => {throw Error('External image loading is disabled');}};
const descriptors = new Map();
function inventory(marks = []) {
  for (const m of marks) {
    if (m.name) {
      if (descriptors.has(m.name)) throw Error('Ambiguous compiled mark name');
      descriptors.set(m.name, {type:m.type, encode:m.encode ?? {}, sort:m.sort ?? null});
    }
    inventory(m.marks);
  }
}
inventory(spec.marks);
let view;
try {
  view = new vega.View(vega.parse(spec), {renderer:'none', loader, logger});
  await view.runAsync();
  if (errors.length) throw Error(errors.join('; '));
  const svg = await view.toSVG();
  const marks = [];
  function channels(item, descriptor) {
    const update = descriptor?.encode?.update ?? {};
    return Object.fromEntries(['x','y','x2','y2','fill','stroke'].map(key => {
      const encoding = update[key];
      if (encoding && typeof encoding.field === 'string') {
        return [key,{kind:'field',field:encoding.field,value:vega.field(encoding.field)(item.datum)}];
      }
      if (encoding && Object.hasOwn(encoding,'value')) {
        return [key,{kind:'constant',value:encoding.value}];
      }
      return [key,{kind:'unresolved'}];
    }));
  }
  function walk(node) {
    if (node.role === 'mark') {
      marks.push({name:node.name, type:node.marktype,
        descriptor:descriptors.get(node.name) ?? null,
        items:(node.items ?? []).map(item => ({datum:item.datum,
          channels:channels(item,descriptors.get(node.name)),
          geometry:Object.fromEntries(['x','y','x2','y2','width','height','defined',
            'opacity','fillOpacity','strokeOpacity','fill','stroke','description']
            .filter(k=>item[k] !== undefined).map(k=>[k,item[k]]))}))});
    }
    for (const child of node.items ?? []) walk(child);
  }
  walk(view.scenegraph().root);
  if (errors.length) throw Error(errors.join('; '));
  process.stdout.write(JSON.stringify({status:'captured',vega_version:vega.version,
    node_version:process.version, marks, svg, warnings}, (_key,value) =>
      typeof value === 'number' && !Number.isFinite(value) ? {nonfinite:String(value)} : value));
} catch (error) {
  process.stdout.write(JSON.stringify({status:'execution_error',error:String(error),warnings,errors}));
  process.exitCode = 1;
} finally {
  view?.finalize();
}
