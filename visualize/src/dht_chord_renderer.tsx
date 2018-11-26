import {DHTChord} from './dht_chord_d3';
import * as React from 'react';

export interface Props { 
  width: number; 
  height: number; 
  m: number;
  peers: number[]; 
  key_id?: number; 
  path?: number[];
}

export class DHTRenderer extends React.Component<Props, {}> {
    public ref!: SVGSVGElement;
    componentDidMount() {
        var chord = new DHTChord(this.ref, this.props.width, this.props.height,
           this.props.m, this.props.peers)
        chord.build_chord()
        if (this.props.key_id && this.props.path) {
          chord.draw_key_path(this.props.key_id, this.props.path)
        }
    }
  
    render() {
      return (
        <svg className="container" ref={(ref: SVGSVGElement) => this.ref = ref}
          width="800" height="800">
        </svg>
      );
    }
  }