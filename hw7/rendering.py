"""Matplotlib playback of saved physics frames; rendering never advances time."""
from Hw5.geometry import world_mesh
from Hw5.spatial import rotate
import os
from pathlib import Path


def render(frames, *, snapshot=None, show=False):
    os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent/'evidence'/'mplconfig'))
    import matplotlib
    if not show:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    figure = plt.figure(figsize=(12.8, 7.2), dpi=100)
    axes = figure.add_subplot(111, projection='3d')
    colors = {'Prism': '#e08c38', 'Sphere': '#359bbe', 'Cylinder': '#926ac0'}

    def draw(world):
        axes.clear()
        for body in world.bodies:
            s = body.state
            faces = [[(x, z, y) for x, y, z in face] for face in world_mesh(body.shape, s.position, s.orientation, 16)]
            color = '#b5bec8' if body.static else colors[type(body.shape).__name__]
            axes.add_collection3d(Poly3DCollection(faces, facecolor=color, edgecolor='#465263',
                                                 linewidth=.3, alpha=.12 if body.static else .88))
            if not body.static:
                d = rotate(s.orientation, (.22, 0, 0))
                p = s.position
                axes.plot((p[0], p[0]+d[0]), (p[2], p[2]+d[2]), (p[1], p[1]+d[1]), color='#b52222', linewidth=1.6)
        axes.set(xlim=(-2.3, 2.3), ylim=(-2.3, 2.3), zlim=(-.2, 5.8),
                 xlabel='world x (m)', ylabel='world z (m)', zlabel='world y (m)',
                 title=f'30 analytic solids | serial contact | t={world.time:.3f} s')
        axes.set_box_aspect((4.6, 4.6, 6.))
        axes.view_init(elev=24, azim=-55)
        return ()

    if snapshot:
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        draw(frames[-1])
        figure.savefig(snapshot)
    if show:
        animation = FuncAnimation(figure, lambda i: draw(frames[i]), frames=len(frames), interval=1000/30, blit=False, repeat=True)
        figure._hw7_animation = animation
        plt.show()
    else:
        plt.close(figure)
