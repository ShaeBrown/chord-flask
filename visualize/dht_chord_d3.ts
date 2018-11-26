import * as d3 from 'd3';
import { node } from 'prop-types';

export class DHTChord {
    public ref: SVGSVGElement;
    private peers: number[];
    private m: number;
    private svg!: d3.Selection<any, any, any, any>;

    constructor(ref: SVGSVGElement, m: number, peers: number[]) {
        this.ref = ref
        this.m = m;
        this.peers = peers
    }

    draw_key_path(key: number, path: number[]) {

    }

    build_chord() {
        var width = 800
        var height = 800
        var cx = width / 2
        var cy = height / 2
        var r = width - 100
        var ticks = 2^this.m
        this.svg = d3.select(this.ref)
            .attr("font-size", 10)
            .attr("font-family", "sans-serif");
        
        this.svg.append("circle")
            .attr("cx", cx)
            .attr("cy", cy)
            .attr("r", r)
            .style("stroke", "black")
            .style("fill", "none")
            .style("stroke-width", 2);

        var nodes = this.svg.append("g")
            .data(this.peers)
            .enter();

        console.log(nodes)
        
        nodes.append("circle")
            .attr("cx", (d) => { 
                return cx + r * Math.sin(d / ticks);
            })
            .attr("cy", (d) => { 
                return cy + r * Math.cos(d / ticks);
            })
           .attr("r", 2);

        nodes.append("text")
            .attr("x", (d) => { 
                return cx + (r+10) * Math.sin(d / ticks);
            })
            .attr("y", (d) => { 
                return cy + (r+10) * Math.cos(d / ticks);
            })
            .text((d) => { return d });
    }
}