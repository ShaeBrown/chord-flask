import {DHTChord} from './dht_chord_d3'

export function render(root: string, width: number, height: number, 
        m: number, peers: number[], key?: number, path?: number[]) {
    var chord = new DHTChord(root, width, height, m, peers)
    chord.build_chord()
    if (key && path) {
       chord.draw_key_path(key, path)
    }
}