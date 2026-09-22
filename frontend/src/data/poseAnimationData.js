/**
 * SVG stick-figure animation data for each pose.
 *
 * Each pose defines an `end` position (the target asana).
 * STANDING is the neutral starting position.
 * All coordinates are within SVG viewBox (0–200 x, 0–280 y).
 * Safe margin: joints kept within x: 14–186, y: 14–265.
 *
 * Joint keys: head, neck, lShoulder, rShoulder, lElbow, rElbow, lWrist, rWrist,
 *             hip, lHip, rHip, lKnee, rKnee, lAnkle, rAnkle
 */

export const STANDING = {
  head:      { x: 100, y: 30 },
  neck:      { x: 100, y: 52 },
  lShoulder: { x: 78,  y: 64 },
  rShoulder: { x: 122, y: 64 },
  lElbow:    { x: 70,  y: 104 },
  rElbow:    { x: 130, y: 104 },
  lWrist:    { x: 68,  y: 142 },
  rWrist:    { x: 132, y: 142 },
  hip:       { x: 100, y: 144 },
  lHip:      { x: 88,  y: 149 },
  rHip:      { x: 112, y: 149 },
  lKnee:     { x: 86,  y: 198 },
  rKnee:     { x: 114, y: 198 },
  lAnkle:    { x: 84,  y: 252 },
  rAnkle:    { x: 116, y: 252 },
};

export const POSE_ANIMATIONS = {
  tadasana: {
    label: "Tadasana (Mountain Pose)",
    end: {
      // Tadasana: perfectly erect spine, arms lightly pressing into sides,
      // feet slightly narrower than STANDING to show the difference.
      head:      { x: 100, y: 24 },
      neck:      { x: 100, y: 46 },
      lShoulder: { x: 80,  y: 56 },
      rShoulder: { x: 120, y: 56 },
      lElbow:    { x: 74,  y: 96 },
      rElbow:    { x: 126, y: 96 },
      lWrist:    { x: 72,  y: 136 },
      rWrist:    { x: 128, y: 136 },
      hip:       { x: 100, y: 138 },
      lHip:      { x: 91,  y: 143 },
      rHip:      { x: 109, y: 143 },
      lKnee:     { x: 90,  y: 194 },
      rKnee:     { x: 110, y: 194 },
      lAnkle:    { x: 90,  y: 248 },
      rAnkle:    { x: 110, y: 248 },
    },
  },

  vrikshasana: {
    label: "Vrikshasana (Tree Pose)",
    end: {
      // Arms overhead, palms pressed together; right foot on inner left thigh.
      head:      { x: 100, y: 22 },
      neck:      { x: 100, y: 44 },
      lShoulder: { x: 82,  y: 56 },
      rShoulder: { x: 118, y: 56 },
      lElbow:    { x: 88,  y: 34 },
      rElbow:    { x: 112, y: 34 },
      lWrist:    { x: 96,  y: 18 },
      rWrist:    { x: 104, y: 18 },
      hip:       { x: 100, y: 138 },
      lHip:      { x: 90,  y: 143 },
      rHip:      { x: 110, y: 143 },
      // Left leg: standing straight
      lKnee:     { x: 88,  y: 194 },
      lAnkle:    { x: 86,  y: 248 },
      // Right leg: raised, foot at inner thigh height
      rKnee:     { x: 136, y: 172 },
      rAnkle:    { x: 104, y: 185 },
    },
  },

  trikonasana: {
    label: "Trikonasana (Triangle Pose)",
    end: {
      // Wide leg stance; hinge at hip; bottom hand toward floor, top arm up.
      head:      { x: 66,  y: 62 },
      neck:      { x: 74,  y: 74 },
      lShoulder: { x: 68,  y: 84 },
      rShoulder: { x: 90,  y: 70 },
      lElbow:    { x: 56,  y: 116 },
      rElbow:    { x: 102, y: 38 },
      lWrist:    { x: 50,  y: 148 },
      rWrist:    { x: 110, y: 18 },
      hip:       { x: 100, y: 142 },
      lHip:      { x: 90,  y: 147 },
      rHip:      { x: 114, y: 142 },
      lKnee:     { x: 60,  y: 198 },
      rKnee:     { x: 140, y: 198 },
      lAnkle:    { x: 46,  y: 252 },
      rAnkle:    { x: 154, y: 252 },
    },
  },

  virabhadrasana_ii: {
    label: "Virabhadrasana II (Warrior II)",
    end: {
      // Front knee bent ~90°; back leg straight; arms extended horizontal.
      head:      { x: 80,  y: 44 },
      neck:      { x: 86,  y: 58 },
      lShoulder: { x: 68,  y: 66 },
      rShoulder: { x: 110, y: 66 },
      lElbow:    { x: 36,  y: 66 },
      rElbow:    { x: 148, y: 66 },
      lWrist:    { x: 18,  y: 66 },
      rWrist:    { x: 178, y: 66 },
      hip:       { x: 100, y: 142 },
      lHip:      { x: 88,  y: 147 },
      rHip:      { x: 114, y: 144 },
      // Front (left) knee bent 90°
      lKnee:     { x: 58,  y: 196 },
      lAnkle:    { x: 44,  y: 252 },
      // Back (right) leg straight
      rKnee:     { x: 144, y: 196 },
      rAnkle:    { x: 158, y: 252 },
    },
  },

  utkatasana: {
    label: "Utkatasana (Chair Pose)",
    end: {
      // Knees bent ~115°, torso leans forward, arms reach overhead by ears.
      head:      { x: 100, y: 22 },
      neck:      { x: 100, y: 44 },
      lShoulder: { x: 82,  y: 54 },
      rShoulder: { x: 118, y: 54 },
      lElbow:    { x: 84,  y: 28 },
      rElbow:    { x: 116, y: 28 },
      lWrist:    { x: 86,  y: 14 },
      rWrist:    { x: 114, y: 14 },
      hip:       { x: 100, y: 156 },
      lHip:      { x: 90,  y: 161 },
      rHip:      { x: 110, y: 161 },
      // Knees bent, sitting back
      lKnee:     { x: 80,  y: 204 },
      rKnee:     { x: 120, y: 204 },
      lAnkle:    { x: 84,  y: 252 },
      rAnkle:    { x: 116, y: 252 },
    },
  },
};

/** Bone connections to draw between joints */
export const SKELETON_CONNECTIONS = [
  ["neck", "head"],
  ["neck", "lShoulder"],
  ["neck", "rShoulder"],
  ["lShoulder", "lElbow"],
  ["lElbow", "lWrist"],
  ["rShoulder", "rElbow"],
  ["rElbow", "rWrist"],
  ["neck", "hip"],
  ["hip", "lHip"],
  ["hip", "rHip"],
  ["lHip", "lKnee"],
  ["lKnee", "lAnkle"],
  ["rHip", "rKnee"],
  ["rKnee", "rAnkle"],
];
