"""Livelier palettes for each section: dusk magenta over Lagos, turquoise sea, bright Atlantic blue, neon server hall."""
IND = ('#5A4BA8', '#463B8E', '#352C73', '#241E55')      # buildings: violet indigo
EXTRA = {
    'sec1_comp': [("gradient_bg(H, W, '#0A0E20', '#2C2140', seed=31)", "gradient_bg(H, W, '#2B1F7E', '#FF8A7A', seed=31)"),
                  ("fog_k=260.0, fog_col='#1E1A30'", "fog_k=560.0, fog_col='#7550A8'"),
                  ("ink='#AFC3DC', ink_k=0.55", "ink='#E6DDFF', ink_k=0.5")],
    'sec2_comp': [("gradient_bg(H, W, '#0C1024', '#3A2A3C', seed=9)", "gradient_bg(H, W, '#2E2380', '#C9608F', seed=9)"),
                  ("gradient_bg(H, W, '#06101E', '#030710', seed=40)", "gradient_bg(H, W, '#0A1B3A', '#050A1E', seed=40)")],
    'sec3_comp': [("gradient_bg(H, W, '#0A0E20', '#2C2140', seed=33)", "gradient_bg(H, W, '#2B1F7E', '#C25A8C', seed=33)"),
                  ("fog_col='#1A1830'", "fog_col='#5A3C8C'"), ("ink='#AFC3DC', ink_k=0.45", "ink='#E6DDFF', ink_k=0.42")],
    'sec5_comp': [("gradient_bg(H, W, '#123560' if t < 19.0 else '#0F2A4C', '#02050B', seed=7)", "gradient_bg(H, W, '#1A8FD0' if t < 19.0 else '#137CC0', '#041A45', seed=7)"),
                  ("god_rays(H, W, 2, 0.24)", "god_rays(H, W, 2, 0.34)")],
    'sec6_comp': [("gradient_bg(H, W, '#0A0C14', '#050608', seed=61)", "gradient_bg(H, W, '#2E1F70', '#140C40', seed=61)"),
                  ("fog_col='#07080C'", "fog_col='#2E1F70'"), ("ink='#7FA6C8'", "ink='#9AB8FF'"),
                  ("(0.15, '#4FA8FF')", "(0.15, '#FF4FD8')")],
    'sec7_comp': [("gradient_bg(H, W, '#0B1220', '#05070C', seed=71)", "gradient_bg(H, W, '#2E2070', '#140C40', seed=71)")],
}
MATS = {
    'sec1_comp': ('M1', {1: ('#3A2F6E', '#2F2660', '#251E50', '#1A1540'), 2: ('#40366F', '#352C60', '#2A2350', '#1F1A40'),
                         12: IND, 13: ('#9AA2D8', '#7E86C0', '#646BA3', '#4A5080'), 14: ('#6A5CC0', '#5649A5', '#433888', '#302868')}),
    'sec2_comp': ('M2', {1: ('#A5623A', '#8A4F2E', '#6E3E24', '#512D1A'), 2: ('#453D78', '#393268', '#2D2756', '#211C44'),
                         3: ('#7A7CB0', '#65679A', '#505282', '#3B3D66'), 12: IND, 14: ('#2A2360', '#231D52', '#1C1744', '#141035'),
                         17: ('#8F86D0', '#7870B6', '#615A9A', '#4A447C')}),
    'sec3_comp': ('M3', {1: ('#3A2F6E', '#2F2660', '#251E50', '#1A1540'), 2: ('#4A4080', '#3D3570', '#312A5E', '#241F4B'),
                         3: ('#C99A5B', '#A97F48', '#876437', '#654A28'), 5: ('#138BA8', '#0F7590', '#0B5E76', '#08475C'),
                         12: IND, 40: ('#9A92D8', '#8078BE', '#675FA2', '#4E4784')}),
    'sec6_comp': ('M6', {50: ('#2B2460', '#251F55', '#1F1A49', '#18143C'), 51: ('#353A85', '#2D3175', '#252864', '#1C1F50'),
                         52: ('#3E4596', '#353B84', '#2C3170', '#22275A'), 53: ('#140F35',)*4, 54: ('#F0E8FF',)*4,
                         55: ('#6E66B8', '#5C55A0', '#4A4486', '#38336A')}),
}
DEEP_MATS = {1: ('#1F8A96', '#18717D', '#125A64', '#0C434B'), 2: ('#223A6A', '#1A2F58', '#132446', '#0D1A34'),
             3: ('#4F74A8', '#3E5F8E', '#2F4B72', '#213857'), 4: ('#1E5A7A', '#174A66', '#113A51', '#0B2A3C'),
             5: ('#4A6FA0', '#3B5A86', '#2D466B', '#203350')}
