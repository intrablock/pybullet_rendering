#pragma once

#include <render/BaseRenderer.h>

#include <scene/SceneGraph.h>
#include <scene/SceneState.h>
#include <scene/SceneView.h>

class PyRenderer : public render::BaseRenderer
{
  public:
    /* Default constructor */
    PyRenderer() {}

    /**
     * @brief Update a scene using \p sceneGraph description
     *
     * @param sceneGraph - scene description
     * @param materialsOnly - update only shape materials
     */
    virtual void updateScene(const scene::SceneGraph& sceneGraph, bool materialsOnly)
    {
        // use "_INT" version as a workaround to pass arguments without copying
        PYBIND11_OVERLOAD_INT(void, render::BaseRenderer, "update_scene", &sceneGraph,
                              &materialsOnly);
    };

    /**
     * @brief Render a scene at state \p sceneState with a view settings \p sceneView
     *
     * @param sceneState - scene state, e.g. transformations of all objects
     * @param sceneView - view settings, e.g. camera, light, viewport size
     * @param outputFrame - rendered images
     *
     * @return True if rendered
     */
    virtual bool renderFrame(const scene::SceneState& sceneState, const scene::SceneView& sceneView,
                             render::FrameData& outputFrame)
    {
        PYBIND11_OVERLOAD_INT(bool, render::BaseRenderer, "render_frame", &sceneState, &sceneView,
                              &outputFrame);
        return false;
    };
};
