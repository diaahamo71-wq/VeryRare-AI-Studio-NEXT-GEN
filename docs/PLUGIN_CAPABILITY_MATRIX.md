# Plugin capability matrix

This matrix describes product requirements, not a claim that every processor is implemented.

| Capability | Current status | Requirement before calling it available |
|---|---|---|
| Gain / vocal-beat balance | Built-in | Unit tests + listening |
| High-pass and gentle presence EQ | Built-in | Response tests + listening |
| Basic compression | Built-in | Dynamics tests + listening |
| Simple room taps / delay | Built-in | Listening and parameter validation |
| Auto-Tune / pitch correction | External plugin required | Verified plugin host + key/scale + test tones |
| Harmonizer / harmony stack | External plugin required | Verified pitch/formant engine + key/chord handling |
| De-esser | External plugin required | Sibilance detector/processor tests |
| Dereverb | External plugin required | Verified restoration processor + artifact A/B |
| Denoise / hum removal | External plugin required | Noise detection + artifact A/B |
| Declipping | External plugin required | Clipped test signals + recovery limits |
| Doubler / vocal stacks | Planned | Pitch/time modulation + mono compatibility checks |
| Saturation / tape | Planned | Gain-matched bypass + oversampling where needed |
| Stereo width | Planned | Phase correlation + mono fold-down |
| Sidechain ducking | Planned | Envelope follower, attack/release and pump tests |
| Section automation / delay throws | Planned | Timeline markers + automation renderer |
| LUFS / true-peak meter | Planned | Standards-compliant measurement tests |
| True-peak limiter | External plugin required | Oversampled limiter + ceiling tests |

## Rule

A capability is only “active” in a specific render when its processor ran successfully. The catalog alone is not proof of execution.
