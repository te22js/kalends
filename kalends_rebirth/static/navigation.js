/* Interruptible intent -> read-only route -> short authoritative steps.
 * A cancelled walk never erases an already committed movement or its time cost.
 * At most one short step is in flight. Presentation can finish that step while
 * the latest destination replaces all remaining, uncommitted intent.
 */
(() => {
  'use strict';
  const length=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  // Older saves retain landmark IDs as public locations. They share the
  // street floor; only a genuine room change may use a whole portal segment.
  const publicScenes=new Set(['street','water','forum_access']);
  const sameScene=(a,b)=>a===b||(publicScenes.has(a)&&publicScenes.has(b));
  class Navigation {
    constructor(callbacks) {
      this.c=callbacks;this.epoch=0;this.intent=null;this.route=[];this.tap=null;
      this.planning=false;this.pending=false;this.destination=null;this.talk=null;
      this.stepLength=48;this.pipelineDistance=12;
    }
    get active(){return Boolean(this.intent||this.route.length||this.tap||this.planning||this.pending);}
    cancel(reason='cancelled') {
      this.epoch++;this.intent=null;this.route=[];this.tap=null;this.destination=null;this.talk=null;
      this.c.trace?.record('navigation_cancel',{reason,step_in_flight:this.pending});
      this.c.changed?.();
    }
    go(body,talk=null) {
      if(this.c.blocked()){this.c.trace?.input('destination',false,'overlay or transaction');return false;}
      this.cancel('new destination');this.intent={body:{...body},epoch:this.epoch};this.talk=talk;
      this.c.clearKeys?.();this.c.trace?.input('destination',true);this.c.started?.();this.pump();return true;
    }
    nudge(dx,dy) {
      if(this.c.blocked()){this.c.trace?.input('direction',false,'overlay or transaction');return false;}
      const magnitude=Math.hypot(dx,dy);if(!magnitude)return false;
      this.cancel('direction change');this.tap={dx:dx/magnitude,dy:dy/magnitude};
      this.c.trace?.input('direction',true);this.c.started?.();this.pump();return true;
    }
    tick() {this.pump();}
    async plan(intent) {
      this.planning=true;
      try {
        const result=await this.c.preview(intent.body);
        if(intent.epoch!==this.epoch)return;
        if(!Array.isArray(result.points)||!result.points.length||result.points.some(p=>!Number.isFinite(p.x)||!Number.isFinite(p.y)||typeof p.location!=='string'))throw Error('The walking route could not be read.');
        this.route=result.points.slice(1).map(p=>({...p}));this.destination={...result.destination};
        this.c.target?.(this.destination);this.c.changed?.();
        if(!this.route.length){this.c.clearKeys?.();this.arrived();}
      } catch(error) {if(intent.epoch===this.epoch){this.cancel('route rejected');this.c.clearKeys?.();this.c.error(error);}}
      finally {this.planning=false;this.pump();}
    }
    arrived() {
      const talk=this.talk;this.talk=null;this.route=[];this.destination=null;
      this.c.changed?.();if(talk)this.c.arrived?.(talk);
    }
    pump() {
      if(this.planning||this.pending||this.c.blocked())return;
      // Limit authority/presentation separation to a short committed step.
      if(this.c.remaining()>this.pipelineDistance)return;
      if(this.intent){const intent=this.intent;this.intent=null;this.plan(intent);return;}
      if(!this.route.length) {
        const direction=this.tap||this.c.direction();this.tap=null;
        if(direction&&(direction.dx||direction.dy)) {
          const p=this.c.position(),magnitude=Math.hypot(direction.dx,direction.dy);
          this.plan({body:{x:p.x+26*direction.dx/magnitude,y:p.y+26*direction.dy/magnitude},epoch:this.epoch});
        } else if(this.talk&&this.c.remaining()<1)this.arrived();
        return;
      }
      const p=this.c.position();let target=this.route[0],distance=length(p,target);
      while(target&&distance<.05&&sameScene(target.location,p.location)){this.route.shift();target=this.route[0];distance=target?length(p,target):0;}
      if(!target){if(this.c.remaining()<1)this.arrived();return;}
      let body;
      if(!sameScene(target.location,p.location))body={x:target.x,y:target.y,location:target.location};
      else if(distance<=this.stepLength)body={x:target.x,y:target.y};
      else body={x:p.x+(target.x-p.x)*this.stepLength/distance,y:p.y+(target.y-p.y)*this.stepLength/distance};
      this.pending=true;const epoch=this.epoch;
      this.c.commit(body).catch(error=>{
        if(epoch===this.epoch){this.cancel('step rejected');this.c.clearKeys?.();this.c.error(error);}
      }).finally(()=>{this.pending=false;this.c.changed?.();this.pump();});
    }
  }
  window.KalendsNavigation=Navigation;
})();
