import {DHTChord} from './dht_chord_d3';
import * as React from 'react';

export interface Props { m: number; peers: number[]; }
export class DHTRenderer extends React.Component<Props, {}> {
    public ref!: SVGSVGElement;
    componentDidMount() {
        var chord = new DHTChord(this.ref, this.props.m, this.props.peers)
        chord.build_chord()
    }
  
    render() {
      return (
        <svg className="container" ref={(ref: SVGSVGElement) => this.ref = ref}
          width="800" height="800">
        </svg>
      );
    }
  }