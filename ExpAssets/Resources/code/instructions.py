import os
import sdl2.sdlmixer as mixer
from sdl2.ext import cursor_hidden

from klibs import P
from klibs.KLUtilities import scale
from klibs.KLTime import CountDown
from klibs.KLEventQueue import pump, flush
from klibs.KLUserInterface import any_key, key_pressed, hide_cursor, show_cursor
from klibs.KLGraphics import fill, flip, blit, NumpySurface
from klibs.KLGraphics import KLDraw as kld
from klibs.KLCommunication import message
from klibs.KLAudio import AudioClip

from animations import Keyframe, Animation
from TraceLabFigure import _render_figure, load_tracing
from InterfaceExtras import Button, Aesthetics, LikertPrompt


IMAGE_ASSETS = [
    "pointer.png",
    "pointer_sml.png",
    "arrow_up.png",
    "arrow_down.png",
    "arrow_right.png",
    "arrow_left.png",
    "dotted_line.png",
    "dotted_curve.png",
    "thought_bubble.png",
    "not_recording.png",
]

AUDIO_FILES = {
    'physical': ["PP1", "PP2", "PP3", "PP4", "PP5", "PP6"],
    'imagery': ["MI1", "MI2", "MI3", "MI4", "MI5", "PP6"],
    'control': ["CC1", "CC2", "CC3", "CC4", "CC5", "CC6", "CC7", "CC8", "CC9"],
}

STIM_LOCS = {
    "origin": (960, 780),
    "shape_p1": (480, 360),
    "shape_p2": (960, 360),
    "shape_c2": (720, 120),
    "shape_p3": (1440, 360),
    "shape_c3": (1200, 120),
    "text_bottom": (960, 900),
    "text_low": (960, 680), # P.screen_y / 0.63
    "text_midlow": (960, 620), # P.screen_y / 0.54
    "text_high": (960, 420),
    "pointer_start": (1070, 900),
    "pointer_pre_origin": (970, 770),
    "pointer_leaves": (824, 696),
    "pointer_near_end": (1050, 710),
    "pointer_miss": (860, 800),
    "not_recording": (960, 340),
    # MI
    "thought_bubble": (1550, 275),
    "mi_origin": (1550, 375),
    "mi_shape_p1": (1400, 200),
    "mi_shape_p2": (1550, 200),
    "mi_shape_c2": (1475, 130),
    "mi_shape_p3": (1700, 200),
    "mi_shape_c3": (1625, 130),
    "pointer_lifted": (990, 830),
    # CC
    "text_top": (960, 150),
    "cc_pointer_start": (960, 1080),
}

ANIMATIONS = {
    'shape1': [0.90, ('origin', 'shape_p1')],
    'shape2': [0.78, ('shape_p1', 'shape_p2', 'shape_c2')],
    'shape3': [0.78, ('shape_p2', 'shape_p3', 'shape_c3')],
    'shape4': [0.90, ('shape_p3', 'origin')],
    'pointer_begin': [0.5, ('pointer_start', 'pointer_lifted')],
    'pointer_click': [0.2, ('pointer_lifted', 'origin')],
    'pointer_leaves': [0.5, ('origin', 'pointer_leaves')],
    # PP-specific animations
    'pointer_to_p1': [0.9, ('origin', 'shape_p1')],
    'pointer_nears_end': [0.9, ('shape_p3', 'pointer_near_end')],
    'pointer_return': [0.5, ('pointer_near_end', 'origin')],
    'pointer_miss': [0.5, ('pointer_near_end', 'pointer_miss')],
    'pointer_recover': [0.5, ('pointer_miss', 'origin')],
    # MI-specific animations
    'mi_shape1': [0.90, ('mi_origin', 'mi_shape_p1')],
    'mi_shape2': [0.78, ('mi_shape_p1', 'mi_shape_p2', 'mi_shape_c2')],
    'mi_shape3': [0.78, ('mi_shape_p2', 'mi_shape_p3', 'mi_shape_c3')],
    'mi_shape4': [0.90, ('mi_shape_p3', 'mi_origin')],
    'pointer_lifted': [0.2, ('origin', 'pointer_lifted')],
    # CC-specific animations
    'shape1_slow': [2.2, ('origin', 'shape_p1')],
    'shape2_slow': [1.2, ('shape_p1', 'shape_p2', 'shape_c2')],
    'shape3_slow': [1.2, ('shape_p2', 'shape_p3', 'shape_c3')],
    'shape4_slow': [1.2, ('shape_p3', 'origin')],
}


class SkipException(Exception):
    # Special exception to allow easy skipping of instructions
    pass


def skip_instructions():
    # Pause any audio clips currently playing and raise exception
    mixer.Mix_HaltChannel(-1)
    raise SkipException('skipping instructions')


def get_demo_resources(condition):
    # Load in and scale instruction images
    images = {}
    for img_file in IMAGE_ASSETS:
        img_path = os.path.join(P.image_dir, img_file)
        img_name = img_file.split(".")[0]
        # Load image and scale to the screen
        img = NumpySurface(img_path)
        scaled_width = int(img.width * (P.screen_x / 1920.0))
        images[img_name] = img.scale(width=scaled_width)

    # Pre-scale stim locations from 1920x1080
    locs = {}
    for name, loc in STIM_LOCS.items():
        locs[name] = scale(loc, (1920, 1080))

    # Pre-generate animations from specified durations/paths
    anims = {}
    for name, anim in ANIMATIONS.items():
        duration, path = anim
        start = locs[path[0]]
        end = locs[path[1]]
        ctrl = locs[path[2]] if len(path) == 3 else None
        anims[name] = Animation(start, end, ctrl, duration)

    # Gather additional stimuli used for instructions
    misc = {}
    demo_segments = [
        (False, (locs['origin'], locs['shape_p1'])),
        (True, (locs['shape_p1'], locs['shape_p2'], locs['shape_c2'])),
        (True, (locs['shape_p2'], locs['shape_p3'], locs['shape_c3'])),
        (False, (locs['shape_p3'], locs['origin']))
    ]
    misc['demo_shape'] = _render_figure(demo_segments)
    demo_tracing = load_tracing(os.path.join(
        P.resources_dir, "figures", "heart", "feedback", "heart_demo.csv"
    ))
    misc['demo_tracing'] = _render_figure(demo_segments, trace=demo_tracing)
    scale_width = int(P.screen_x * 0.60)
    scale_aes = Aesthetics(fill=(128, 128, 128, 64), fontstyle="large")
    misc['demo_scale'] = LikertPrompt(
        1, 10, message(" "), width=scale_width, origin=P.screen_c, aes=scale_aes
    ).scale

    return (images, locs, anims, misc)


def run_animations(anims, stim_set=[], audio=None):

    # If an audio clip was provided, start playing if it isn't playing already
    if audio and not audio.playing:
        audio.play()

    # Run each given animation/keyframe in sequence
    for keyframe in anims:
        # If keyframe has 3 elements, middle element is custom blit registration
        if len(keyframe) == 3:
            stim, a_reg, a = keyframe
        else:
            stim, a = keyframe
            a_reg = 5
        
        # Run animation until complete, drawing any background stimuli
        a.reset()
        while not a.done:
            fill()

            # Draw background stimuli
            for x in stim_set:
                # If background stimulus has blit() method, use that to draw it
                if hasattr(x, 'blit'):
                    x.blit()
                else:
                    # If stim has 3 elements, middle item is blit registration
                    if len(x) == 3:
                        s, reg, loc = x
                    else:
                        s, loc = x
                        reg = 5
                    blit(s, reg, loc)
            
            # Draw animated stimulus (if any) at its current position
            if stim is None:
                # Still need to increment timer on empty keyframe
                a.position
            else:
                blit(stim, a_reg, a.position)

            # Redraw the scren and check for any keyboard input
            flip()
            if key_pressed('delete'):
                skip_instructions()


def show_demo_screen(
        msg=" ", stim_set=[], duration=0.1, msg_y=None, button=None
    ):
    """Draws text and stimuli onto the screen for task instructions."""

    msg_x = int(P.screen_x / 2)
    msg_y = int(P.screen_y * 0.5) if msg_y is None else msg_y
    txt = message(msg, align="center")
    
    # Draw text/stimuli to the screen for given duration, optionally waiting for
    # input before continuing
    waiting = True if button else False
    t = CountDown(duration)
    while (t.counting() or waiting):
        q = pump()
        fill()
        for stim, loc in stim_set:
            if isinstance(loc, Animation):
                blit(stim, 5, loc.position)
            elif hasattr(stim, 'blit') and not isinstance(stim, NumpySurface):
                stim.blit()
            else:
                blit(stim, 5, loc)
        blit(txt, 5, (msg_x, msg_y))
        if button:
            button.draw()
            if not t.counting():
                waiting = button.listen(q) == False
        flip()
        if key_pressed('delete', queue=q):
            skip_instructions()


def task_demo_pp_practice(exp):

    # Initialize task stimuli for the demo
    images, locs, anims, misc = get_demo_resources('physical')
    white_dot = exp.tracker_dot
    origin_red = exp.origin_inactive
    origin_green = exp.origin_active
    txt_low = locs['text_bottom'][1]
    txt_mid = P.screen_y // 2
    next_loc = (P.screen_x - 75, P.screen_y - 75)
    next_aes = Aesthetics(fill = (255, 255, 255, 64))
    next_btn = Button(
        "Continue", 160, 80, aes=next_aes, registration=3, location=next_loc
    )

    # Show initial set of welcome instructions
    show_demo_screen(
        ("Welcome to the experiment!\n\n"
         "This tutorial will explain how the task works. When you're ready, tap "
         "the 'continue' button to begin."),
        button=next_btn
    )
    show_demo_screen(
        ("The purpose of this task is to test your fine motor skills and see how well "
         "you can learn complex movements.\n\nOn each trial, you will see a dot trace "
         "out a shape. When the dot disappears, your job will be\nto reproduce the "
         "dot's movements yourself using the touchscreen."),
        button=next_btn
    )

    # Explain what the onset of a trial looks like
    show_demo_screen(
        "At the start of each trial, you will be shown the full path the dot will trace.",
        [(misc['demo_shape'], P.screen_c), (white_dot, locs['origin'])],
        msg_y=txt_low, button=next_btn
    )
    show_demo_screen(
        "The shape will disappear, and the white dot will quickly trace along its path.",
        [(white_dot, locs['origin'])],
        msg_y=txt_low, button=next_btn
    )

    # Show an example of what the figure animation looks like
    run_animations([
        (white_dot, Keyframe(locs['origin'], duration=0.5)),
        (white_dot, anims['shape1']),
        (white_dot, anims['shape2']),
        (white_dot, anims['shape3']),
        (white_dot, anims['shape4']),
    ])

    # Explain basics of task, show hand pointer moving to origin
    show_demo_screen(
        ("Each tracing begins and ends at the same point. When the animation ends, a "
         "red circle will appear\n"
         "at the tracing's start point, indicating you are able to respond."),
        [(origin_red, locs['origin'])], msg_y=txt_mid, button=next_btn
    )
    show_demo_screen(
        ("For this part of the study, your job will be to trace out the dot's "
         "movements physically on the\n"
         "touchscreen, trying your best to match its path as well as its speed."),
        [(origin_red, locs['origin'])], msg_y=txt_mid, button=next_btn
    )

    # Explain how to start a trial
    instructions_4 = message(
        ("When you're ready, place and hold your index finger on the red circle to "
         "begin.\n\nNote that you do not need to start tracing right away. Take your "
         "time!"),
        align='center'
    )
    run_animations([
        (images['pointer'], Keyframe(locs['pointer_start'], duration=0.3)),
        (images['pointer'], anims['pointer_begin'])
    ],
        stim_set=[(origin_red, locs['origin']), (instructions_4, P.screen_c)]
    )
    show_demo_screen(
        stim_set=[
            (instructions_4, P.screen_c),
            (origin_red, locs['origin']),
            (images['pointer'], locs['pointer_lifted'])
        ], msg_y=txt_mid, button=next_btn
    )
    instructions_5 = message(
        ("When you touch the circle it will turn green, indicating the touchscreen is "
         "recording.\n\nWhen you're ready, try your best to trace out the dot's "
         "movements using your index finger,\nmatching the path and speed as closely "
         "as possible."),
        align='center'
    )
    run_animations([
        (images['pointer'], anims['pointer_click'])
    ],
        stim_set=[(origin_red, locs['origin']), (instructions_5, P.screen_c)]
    )
    show_demo_screen(
        stim_set=[
            (instructions_5, P.screen_c),
            (origin_green, locs['origin']),
            (images['pointer'], locs['origin'])
        ],
        msg_y=txt_mid, button=next_btn
    )

    # Show the hand pointer tracing the figure, stopping before touching origin
    run_animations([
        (images['pointer'], anims['pointer_to_p1']),
        (images['pointer'], anims['shape2']),
        (images['pointer'], anims['shape3']),
        (images['pointer'], anims['pointer_nears_end']),
    ],
        stim_set=[(origin_green, locs['origin'])]
    )

    # Illustrate what it looks like to successfully end a trial
    pp_instr_6 = (
        "The trial ends when your finger returns to the green circle.\n\n"
        "When you end a trial successfully, the circle will disappear."
    )
    instructions_6 = (message(pp_instr_6, align='center'), P.screen_c)
    show_demo_screen(
        stim_set=[
            instructions_6,
            (origin_green, locs['origin']),
            (images['pointer'], locs['pointer_near_end']),
        ],
        button=next_btn
    )
    run_animations(
        [(images['pointer'], anims['pointer_return'])],
        stim_set=[(origin_green, locs['origin']), instructions_6]
    )
    show_demo_screen(
        stim_set=[instructions_6, (images['pointer'], locs['origin'])],
        button=next_btn
    )

    # Illustrate what it looks like to accidentally miss the origin and how to
    # correct for this if it happens
    pp_instr_7 = (
        "If you finish tracing but still see the green circle, simply drag your\n"
        "finger onto the circle again to end the trial."
    )
    instructions_7 = (message(pp_instr_7, align='center'), P.screen_c)
    run_animations([
        (images['pointer'], anims['pointer_miss']),
        (images['pointer'], Keyframe(locs['pointer_miss'], duration=1.0)),
        (images['pointer'], anims['pointer_recover']),
    ],
        stim_set=[(origin_green, locs['origin']), instructions_7]
    )
    show_demo_screen(
        stim_set=[instructions_7, (images['pointer'], locs['origin'])],
        button=next_btn
    )

    # Illustrate what it looks like if the trial didn't start successfully
    show_demo_screen(
        ("If you notice at any point during the tracing that the circle is still red, "
         "this means\nthe trial didn't start correctly and your movement is not "
         "recording."),
        stim_set=[
            (origin_red, locs['origin']),
            (images['pointer'], locs['pointer_near_end']),
        ],
        button=next_btn
    )
    pp_instr_8 = (
        "If this happens, return to the starting circle and make sure it turns green "
        "before trying again."
    )
    instructions_8 = (message(pp_instr_8, align='center'), P.screen_c)
    run_animations([
        (None, Keyframe(None, duration=0.8)),
        (images['pointer'], Keyframe(locs['pointer_lifted'], duration=0.2)),
        (images['pointer'], anims['pointer_click']),
    ],
        stim_set=[(origin_red, locs['origin']), instructions_8]
    )
    show_demo_screen(
        stim_set=[
            instructions_8,
            (origin_green, locs['origin']),
            (images['pointer'], locs['origin']),
        ],
        button=next_btn
    )

    # Explain feedback for insufficient tracing pressure
    default_fill_bak = P.default_fill_color
    P.default_fill_color = (128, 16, 16, 255)
    show_demo_screen(
        ("If the touchscreen loses track of your finger at any point during the "
         "tracing,\nthe background will turn red until your finger returns to the "
         "screen.\n\nIf this happens repeatedly, try using more pressure!"),
        button=next_btn
    )
    P.default_fill_color = default_fill_bak

    # Explain different types of trial feedback
    show_demo_screen(
        ("At the end of each trial, you will be given a moment to reflect on your "
         "performance."),
        button=next_btn
    )
    show_demo_screen(
        ("On some trials you will be shown your tracing (in blue) overlayed on top of "
         "the target path,\nallowing you to see how closely you matched the dot's "
         "movements."),
        [(misc['demo_tracing'], P.screen_c)],
        msg_y=txt_low, button=next_btn
    )
    show_demo_screen(
        ("On other trials you will only be shown the target path itself, allowing for "
         "mental\ncomparison of your tracing with the dot's movements."),
        [(misc['demo_shape'], P.screen_c)],
        msg_y=txt_low, button=next_btn
    )
    show_demo_screen(
        ("On some trials you will be shown a blank screen without any feedback.\n"
         "For these trials, simply reflect on how well you think you drew the "
         "target shape."),
        msg_y=txt_low, button=next_btn
    )

    # Show final screen of instructions
    show_demo_screen(
        "Now it's your turn. Try some practice trials!",
        button=next_btn
    )


def task_demo_mi(exp):

    # Initialize task stimuli for the demo
    images, locs, anims, misc = get_demo_resources('imagery')
    white_dot = exp.tracker_dot
    origin_red = exp.origin_inactive
    origin_green = exp.origin_active
    thought_bubble = (images['thought_bubble'], locs['thought_bubble'])
    txt_midlow = locs['text_midlow'][1]
    txt_low = locs['text_bottom'][1]
    txt_mid = P.screen_y // 2
    txt_high = locs['text_high'][1]
    next_loc = (P.screen_x - 75, P.screen_y - 75)
    next_aes = Aesthetics(fill = (255, 255, 255, 64))
    next_btn = Button(
        "Continue", 160, 80, aes=next_aes, registration=3, location=next_loc
    )

    # Show initial set of imagery instructions
    show_demo_screen(
        ("Now that you've had a chance to practice the task physically, you will "
         "continue to practice\ntracing movements *mentally* using motor imagery.\n\n"
         "This means that instead of tracing the dot's path physically, you will be "
         "asked to simulate tracing\nthe movements mentally as a form of practice."),
        button=next_btn
    )
    show_demo_screen(
        ("At the end of the study, you will be tested on how well you can trace "
         "these movements physically.\nTry your best to use this mental practice "
         "phase to improve your future performance."),
        button=next_btn
    )

    # Explain what the onset of a trial looks like
    show_demo_screen(
        ("Just as before, each trial will start with a dot tracing a path on the "
         "screen. When the animation ends,\na red circle will appear at the tracing's "
         "start point, indicating you are able to respond."),
        [(origin_red, locs['origin'])], msg_y=txt_mid, button=next_btn
    )
    show_demo_screen(
        ("For this part of the study, your job will be to practice tracing out the "
         "dot's movements *mentally*,\nkeeping your finger and arm still as you "
         "imagine performing the movements involved."),
        [(origin_red, locs['origin'])], msg_y=txt_mid, button=next_btn
    )

    instructions_4 = message(
        ("When you're ready, place and hold your index finger on the red circle to "
         "begin.\n\nAs before, you do not need to respond right away. Take your "
         "time!"),
        align='center'
    )
    show_demo_screen(
        stim_set=[
            (instructions_4, P.screen_c),
            (origin_red, locs['origin']),
            (images['pointer'], locs['pointer_lifted'])
        ], msg_y=txt_mid, button=next_btn
    )

    instructions_5 = message(
        ("As soon as you touch the circle, stop moving and *imagine* performing the "
         "movements needed\nto trace out the dot's path, trying your best to match "
         "the path and speed of the dot."),
        align='center'
    )
    run_animations([
        (images['pointer'], anims['pointer_click']),
    ],
        stim_set = [
            (instructions_5, locs['text_midlow']),
            (origin_red, locs['origin']),
        ]
    )
    show_demo_screen(
        stim_set = [
            (instructions_5, locs['text_midlow']),
            (origin_green, locs['origin']),
            (images['pointer'], locs['origin'])
        ],
        duration=1.0
    )
    show_demo_screen(
        stim_set = [
            (instructions_5, locs['text_midlow']),
            (origin_green, locs['origin']),
            (images['pointer'], locs['origin']),
            thought_bubble,
            (images['pointer_sml'], locs['mi_origin']),
        ],
        msg_y=txt_mid, button=next_btn
    )
    run_animations([
        (images['pointer_sml'], Keyframe(locs['mi_origin'], duration=0.2)),
        (images['pointer_sml'], anims['mi_shape1']),
        (images['pointer_sml'], anims['mi_shape2']),
        (images['pointer_sml'], anims['mi_shape3']),
    ],
        stim_set = [
            (instructions_5, locs['text_midlow']),
            (origin_green, locs['origin']),
            (images['pointer'], locs['origin']),
            thought_bubble
        ]
    )

    background_stim = [
        (origin_green, locs['origin']),
        (images['pointer'], locs['origin']),
        thought_bubble,
    ]
    show_demo_screen(
        ("Think about the movements you would need to make to trace out the dot's "
         "path, as well as\nwhat those movements would look like and how they would "
         "feel."),
        stim_set = background_stim + [(images['pointer_sml'], locs['mi_shape_p3'])],
        msg_y=txt_midlow, button=next_btn
    )

    # Illustrate what it looks like to successfully end a trial
    mi_instr_7 = (
        "When you imagine yourself returning to the green starting point to finish "
        "tracing,\nlift your finger from the screen to end the trial."
    )
    instructions_7 = (message(mi_instr_7, align='center'), locs['text_midlow'])
    run_animations([
        # Show hand pointer returning to origin
        (images['pointer_sml'], Keyframe(locs['mi_shape_p3'], duration=0.5)),
        (images['pointer_sml'], anims['mi_shape4'])
    ],
        stim_set = background_stim + [instructions_7, (images['pointer'], locs['origin'])]
    )
    run_animations([
        # Show hand pointer returning to origin
        (images['pointer'], Keyframe(locs['origin'], duration=1.0)),
        (images['pointer'], anims['pointer_lifted'])
    ],
        stim_set = [instructions_7, (origin_green, locs['origin'])]
    )
    show_demo_screen(
        stim_set=[instructions_7, (images['pointer'], locs['pointer_lifted'])],
        button=next_btn
    )

    # Explain different types of trial feedback
    show_demo_screen(
        ("At the end of each trial, you will be given a moment to reflect on your "
         "performance."),
        button=next_btn
    )
    show_demo_screen(
        ("On some trials you will be shown your *expected performance* at this stage "
        "of learning (in blue)\noverlayed on top of the target shape."),
        [(misc['demo_tracing'], P.screen_c)],
        msg_y=txt_low, button=next_btn
    )
    show_demo_screen(
        ("Afterwards, you will be asked to rate how closely your imagined tracing "
         "matched\nthe expected performance (the blue overlay) on a scale from 1 to 10."),
        stim_set=[(misc['demo_scale'], P.screen_c)],
        msg_y=txt_high, button=next_btn
    )
    show_demo_screen(
        ("On other trials you will only be shown the target path itself, allowing for "
         "mental\ncomparison of your imagined performance with the ideal trajectory."),
        [(misc['demo_shape'], P.screen_c)],
        msg_y=txt_low, button=next_btn
    )
    show_demo_screen(
        ("Afterwards, you will be asked to rate how closely your imagined tracing "
         "matched\nthe *target shape* on a scale from 1 to 10."),
        stim_set=[(misc['demo_scale'], P.screen_c)],
        msg_y=txt_high, button=next_btn
    )
    show_demo_screen(
        ("On some trials you will be shown a blank screen without any feedback.\n"
         "For these trials, simply reflect on how closely you think your imagined "
         "tracing matched the target shape."),
        msg_y=txt_low, button=next_btn
    )
    show_demo_screen(
        ("Afterwards, you will be asked to rate how accurate you think your imagined "
         "tracing\nwas on a scale from 1 to 10."),
        stim_set=[(misc['demo_scale'], P.screen_c)],
        msg_y=txt_high, button=next_btn
    )

    # Show final screen of instructions
    show_demo_screen(
        "Now it's your turn. Try some practice trials!",
        button=next_btn
    )


def task_demo_pp(exp):

    # Initialize task stimuli for the demo
    images, locs, anims, misc = get_demo_resources('physical')
    white_dot = exp.tracker_dot
    origin_red = exp.origin_inactive
    origin_green = exp.origin_active
    txt_low = locs['text_bottom'][1]
    txt_mid = P.screen_y // 2
    txt_high = locs['text_high'][1]
    next_loc = (P.screen_x - 75, P.screen_y - 75)
    next_aes = Aesthetics(fill = (255, 255, 255, 64))
    next_btn = Button(
        "Continue", 160, 80, aes=next_aes, registration=3, location=next_loc
    )

    # Show initial set of welcome instructions
    show_demo_screen(
        ("Now that you have practiced the different movements extensively,\n"
         "you will be tested on your fine motor performance."),
        button=next_btn
    )

    # Explain what the onset of a trial looks like
    show_demo_screen(
        ("For this part of the study, your job will be to trace out the dot's "
         "movements *physically* on the\n"
         "touchscreen, trying your best to match its path as well as its speed."),
        [(origin_red, locs['origin'])], msg_y=txt_mid, button=next_btn
    )

     # Explain how to start a trial
    instructions_4 = message(
        ("When you're ready, place and hold your index finger on the red circle to "
         "begin.\n\nNote that you do not need to start tracing right away. Take your "
         "time!"),
        align='center'
    )
    run_animations([
        (images['pointer'], Keyframe(locs['pointer_start'], duration=0.3)),
        (images['pointer'], anims['pointer_begin'])
    ],
        stim_set=[(origin_red, locs['origin']), (instructions_4, P.screen_c)]
    )
    show_demo_screen(
        stim_set=[
            (instructions_4, P.screen_c),
            (origin_red, locs['origin']),
            (images['pointer'], locs['pointer_lifted'])
        ], msg_y=txt_mid, button=next_btn
    )
    instructions_5 = message(
        ("When you touch the circle it will turn green, indicating the touchscreen is "
         "recording.\n\nWhen you're ready, try your best to trace out the dot's "
         "movements using your index finger,\nmatching the path and speed as closely "
         "as possible."),
        align='center'
    )
    run_animations([
        (images['pointer'], anims['pointer_click'])
    ],
        stim_set=[(origin_red, locs['origin']), (instructions_5, P.screen_c)]
    )
    show_demo_screen(
        stim_set=[
            (instructions_5, P.screen_c),
            (origin_green, locs['origin']),
            (images['pointer'], locs['origin'])
        ],
        msg_y=txt_mid, button=next_btn
    )

    # Show the hand pointer tracing the figure, stopping before touching origin
    run_animations([
        (images['pointer'], anims['pointer_to_p1']),
        (images['pointer'], anims['shape2']),
        (images['pointer'], anims['shape3']),
        (images['pointer'], anims['pointer_nears_end']),
    ],
        stim_set=[(origin_green, locs['origin'])]
    )

    # Illustrate what it looks like to successfully end a trial
    pp_instr_6 = (
        "The trial ends when your finger returns to the green circle.\n\n"
        "When you end a trial successfully, the circle will disappear."
    )
    instructions_6 = (message(pp_instr_6, align='center'), P.screen_c)
    show_demo_screen(
        stim_set=[
            instructions_6,
            (origin_green, locs['origin']),
            (images['pointer'], locs['pointer_near_end']),
        ],
        button=next_btn
    )
    run_animations(
        [(images['pointer'], anims['pointer_return'])],
        stim_set=[(origin_green, locs['origin']), instructions_6]
    )
    show_demo_screen(
        stim_set=[instructions_6, (images['pointer'], locs['origin'])],
        button=next_btn
    )

    # Illustrate what it looks like to accidentally miss the origin and how to
    # correct for this if it happens
    pp_instr_7 = (
        "If you finish tracing but still see the green circle, simply drag your\n"
        "finger onto the circle again to end the trial."
    )
    instructions_7 = (message(pp_instr_7, align='center'), P.screen_c)
    run_animations([
        (images['pointer'], anims['pointer_miss']),
        (images['pointer'], Keyframe(locs['pointer_miss'], duration=1.0)),
        (images['pointer'], anims['pointer_recover']),
    ],
        stim_set=[(origin_green, locs['origin']), instructions_7]
    )
    show_demo_screen(
        stim_set=[instructions_7, (images['pointer'], locs['origin'])],
        button=next_btn
    )

    # Illustrate what it looks like if the trial didn't start successfully
    show_demo_screen(
        ("If you notice at any point during the tracing that the circle is still red, "
         "this means\nthe trial didn't start correctly and your movement is not "
         "recording."),
        stim_set=[
            (origin_red, locs['origin']),
            (images['pointer'], locs['pointer_near_end']),
        ],
        button=next_btn
    )
    pp_instr_8 = (
        "If this happens, return to the starting circle and make sure it turns green "
        "before trying again."
    )
    instructions_8 = (message(pp_instr_8, align='center'), P.screen_c)
    run_animations([
        (None, Keyframe(None, duration=0.8)),
        (images['pointer'], Keyframe(locs['pointer_lifted'], duration=0.2)),
        (images['pointer'], anims['pointer_click']),
    ],
        stim_set=[(origin_red, locs['origin']), instructions_8]
    )
    show_demo_screen(
        stim_set=[
            instructions_8,
            (origin_green, locs['origin']),
            (images['pointer'], locs['origin']),
        ],
        button=next_btn
    )

    # Explain feedback for insufficient tracing pressure
    default_fill_bak = P.default_fill_color
    P.default_fill_color = (128, 16, 16, 255)
    show_demo_screen(
        ("If the touchscreen loses track of your finger at any point during the "
         "tracing,\nthe background will turn red until your finger returns to the "
         "screen.\n\nIf this happens repeatedly, try using more pressure!"),
        button=next_btn
    )
    P.default_fill_color = default_fill_bak

    # Explain different types of trial feedback
    show_demo_screen(
        ("In this phase of the study, you will not receive any feedback on your "
         "performance."),
        button=next_btn
    )

    # Explain rating scales
    show_demo_screen(
        ("After each tracing, you will be asked to rate how *accurate* you thought "
         "your tracing was on a scale from 1 to 10."),
        stim_set=[(misc['demo_scale'], P.screen_c)],
        msg_y=txt_high, button=next_btn
    )

    # Show final screen of instructions
    show_demo_screen(
        "Now it's your turn. Try some practice trials!",
        button=next_btn
    )


def task_session_resume():

    # Initialize stimuli for the resume study message
    txt_mid = P.screen_y // 2
    next_loc = (P.screen_x - 75, P.screen_y - 75)
    next_aes = Aesthetics(fill = (255, 255, 255, 64))
    next_btn = Button(
        "Continue", 160, 80, aes=next_aes, registration=3, location=next_loc
    )

    show_demo_screen(
        ("Welcome back to the study!\n\nIn this session, you will continue to "
         "practice the task *mentally*,\nsimulating the movements required to trace "
         "out the dot's path."),
        button=next_btn
    )
    show_demo_screen(
        ("Remember to keep your hand and arm still as you think about how it would "
         "look and feel to\nphysically trace out the dot's movements.\n\nTo replay "
         "the instructions for the task, press the 'Replay' button on the next "
         "screen.\nOtherwise, press 'Practice' to try a practice trial or 'Begin' to "
         "start the session."),
        button=next_btn
    )



def play_tutorial(exp, block_type):

    cursor_was_shown = cursor_hidden() == False
    hide_cursor()
    try:
        if block_type == "Practice":
            task_demo_pp_practice(exp)
        elif block_type == "F3":
            task_demo_mi(exp)
        elif block_type == "XX":
            task_demo_pp(exp)
        elif block_type == "resume":
            task_session_resume()
        else:
            e = "Unknown block type '{0}'"
            raise RuntimeError(e.format(block_type))
    except SkipException:
        # Instructions can be skipped by pressing the delete key
        pass

    # If cursor was visible before tutorial, unhide it after
    if cursor_was_shown:
        show_cursor()
